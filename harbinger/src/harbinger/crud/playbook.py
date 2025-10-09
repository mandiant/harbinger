import contextlib
import json
import uuid
from collections.abc import Iterable
from datetime import timedelta

import jinja2
import yaml
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from pydantic import UUID4, TypeAdapter, ValidationError
from sqlalchemy import Select, delete, exc, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas
from harbinger.database.redis_pool import redis
from harbinger.proto.v1 import messages_pb2

from ._common import create_filter_for_column, env, to_excel
from .c2_job import clone_c2_job, create_c2_job
from .file import delete_input_files
from .label import (
    create_label,
    create_label_item,
    delete_label_item,
    get_label_by_name,
    get_labeled_items_list,
    get_labels_for_q,
)
from .process import _process_dynamic_argument_ids
from .proxy_job import clone_proxy_job, create_proxy_job


async def preview_chain_from_template(
    db: AsyncSession,
    chain: schemas.PlaybookTemplate,
    arguments: dict,
) -> dict:
    labels = await get_labeled_items_list(
        db,
        c2_implant_id=arguments.get("c2_implant"),
        retrieve_parents=True,
    )
    await _process_dynamic_argument_ids(db, arguments)
    result = {"steps": "", "valid": False, "errors": "", "steps_errors": ""}
    try:
        value_template = env.from_string(chain.steps or "")
        steps_str = await value_template.render_async(**arguments, labels=labels)
        steps_dict = yaml.safe_load(steps_str)
        StepValidator = TypeAdapter(list[schemas.Step])
        result = {"steps": steps_str, "valid": False}
        try:
            StepValidator.validate_python(steps_dict)
            result["valid"] = True
        except ValidationError as e:
            result["steps_errors"] = e.json()
        except Exception:
            pass
    except jinja2.exceptions.TemplateSyntaxError as e:
        result["errors"] = str(e)
    except jinja2.exceptions.UndefinedError as e:
        result["errors"] = str(e)
    except Exception as e:
        result["errors"] = str(e)
    return result


async def create_chain_from_template(
    db: AsyncSession,
    chain: schemas.PlaybookTemplate,
    arguments: dict,
) -> models.Playbook:
    labels = await get_labeled_items_list(
        db,
        c2_implant_id=arguments.get("c2_implant"),
        retrieve_parents=True,
    )
    await _process_dynamic_argument_ids(db, arguments)
    value_template = env.from_string(chain.steps or "")
    steps_str = await value_template.render_async(**arguments, labels=labels)
    steps_dict = yaml.safe_load(steps_str)
    StepValidator = TypeAdapter(list[schemas.Step])
    steps: list[schemas.Step] = StepValidator.validate_python(steps_dict)
    playbook_obj = models.Playbook(
        playbook_name=chain.name,
        status=schemas.Status.created,
        arguments=json.loads(json.dumps(arguments, default=lambda o: "")),
        steps=len(steps),
        completed=0,
        playbook_template_id=chain.id,
    )
    db.add(playbook_obj)
    await db.commit()
    await db.refresh(playbook_obj)
    playbook_id = playbook_obj.id
    count = 1
    for step in steps:
        step_delay = timedelta(seconds=step.delay or 0)
        job = None
        proxy_job_id = None
        c2_job_id = None
        extra_args = {}
        for arg in step.args or []:
            extra_args[arg.name] = arg.value
        if step.type == schemas.C2Type.proxy:
            from harbinger.job_templates.proxy import PROXY_JOB_BASE_MAP

            args = {**arguments, **extra_args}
            proxy_job = PROXY_JOB_BASE_MAP[step.name](**args)
            job_db = await create_proxy_job(
                db,
                schemas.ProxyJobCreate(
                    command=await proxy_job.generate_command(),
                    proxy_id=arguments.get("proxy_id"),
                    arguments=await proxy_job.generate_arguments(db),
                    input_files=await proxy_job.files(db),
                    socks_server_id=proxy_job.socks_server_id,
                    tmate=step.tmate,
                    asciinema=step.asciinema,
                    proxychains=step.proxychains,
                ),
            )
            proxy_job_id = job_db.id
        elif step.type == schemas.C2Type.c2:
            from harbinger.job_templates.schemas import C2_JOB_BASE_MAP

            job = C2_JOB_BASE_MAP[step.name](**{**arguments, **extra_args})
            job_db = await create_c2_job(
                db,
                schemas.C2JobCreate(
                    command=job.Settings.command,
                    arguments=await job.generate_arguments(db),
                    input_files=await job.files(db),
                    playbook_id=str(playbook_id),
                    c2_implant_id=job.c2_implant_id,
                    add_labels=getattr(job.Settings, "add_labels", None),
                ),
            )
            c2_job_id = job_db.id
        step_db = await add_step(
            db,
            step=schemas.ChainStepCreate(
                playbook_id=str(playbook_id),
                number=count,
                delay=step_delay,
                proxy_job_id=proxy_job_id,
                c2_job_id=c2_job_id,
                label=step.label,
                depends_on=step.depends_on,
            ),
            add_depends_on=chain.add_depends_on,
        )
        if step.modifiers:
            for modifier in step.modifiers:
                data = modifier.model_dump()
                data["playbook_step_id"] = step_db.id
                await create_playbook_step_modifier(
                    db,
                    schemas.PlaybookStepModifierCreate(**data),
                )
        count += 1
    await db.commit()
    await db.refresh(playbook_obj)
    return playbook_obj


async def create_chain(
    db: AsyncSession,
    chain: schemas.ProxyChainCreate,
) -> models.Playbook:
    db_chain = models.Playbook(**chain.model_dump())
    db_chain.status = schemas.Status.created
    db_chain.steps = 0
    db_chain.completed = 0
    db.add(db_chain)
    await db.commit()
    await db.refresh(db_chain)
    return db_chain


async def clone_chain(
    db: AsyncSession,
    chain: models.Playbook | schemas.ProxyChainGraph,
) -> models.Playbook:
    new_chain = models.Playbook(
        playbook_name=f"Clone of {chain.playbook_name}",
        description=chain.description,
        status=schemas.Status.created,
        arguments=chain.arguments,
        steps=chain.steps,
        completed=0,
    )
    db.add(new_chain)
    await db.commit()
    await db.refresh(new_chain)
    steps = await get_playbook_steps(db, 0, 10000000, str(chain.id))
    for step in steps:
        await clone_chain_step(db, step, str(new_chain.id))
    await db.refresh(new_chain)
    return new_chain


async def get_playbooks(
    db: AsyncSession,
    filters: filters.PlaybookFilter,
    offset: int = 0,
    limit: int = 0,
) -> Iterable[models.Playbook]:
    q: Select = select(models.Playbook).outerjoin(models.Playbook.labels).group_by(models.Playbook.id)
    q = q.outerjoin(models.Playbook.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def update_chain(
    db: AsyncSession,
    playbook_id: str,
    chain: schemas.ProxyChainCreate,
) -> models.Playbook | None:
    db_chain = await db.get(models.Playbook, playbook_id)
    if db_chain:
        db_chain.playbook_name = chain.playbook_name
        db_chain.description = chain.description
        db.add(db_chain)
        await db.commit()
        await db.refresh(db_chain)
    await send_update_playbook(playbook_id, "updated_chain")
    return db_chain


async def send_update_playbook(playbook_id: str, event_name: str, id: str = ""):
    msg = messages_pb2.Event(event=event_name, id=id)
    await redis.publish(f"playbook_stream_{playbook_id}", msg.SerializeToString())


async def get_playbooks_paged(
    db: AsyncSession,
    filters: filters.PlaybookFilter,
) -> Page[models.Playbook]:
    q: Select = select(models.Playbook)
    q = q.outerjoin(models.Playbook.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Playbook.id)
    return await apaginate(db, q)


async def get_playbooks_filters(db: AsyncSession, filters: filters.PlaybookFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Playbook.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["playbook_name", "status"]:
        res = await create_filter_for_column(
            db,
            q,
            getattr(models.Playbook, field),
            field,
            field,
        )
        result.append(res)
    return result


async def get_playbook(db: AsyncSession, id: UUID4 | str) -> models.Playbook | None:
    return await db.get(models.Playbook, id)


async def get_chains(db: AsyncSession) -> Page[models.Playbook]:
    return await apaginate(
        db,
        select(models.Playbook).order_by(models.Playbook.time_created.desc()),
    )


async def get_chain_steps_paged(
    db: AsyncSession,
    playbook_id: str = "",
) -> Page[models.PlaybookStep]:
    q = select(models.PlaybookStep)
    if playbook_id:
        q = q.where(models.PlaybookStep.playbook_id == playbook_id)
    q = q.order_by(models.PlaybookStep.number.asc())
    return await apaginate(db, q)


async def get_playbook_steps(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 10,
    playbook_id: str | uuid.UUID = "",
) -> Iterable[models.PlaybookStep]:
    q = select(models.PlaybookStep)
    if playbook_id:
        q = q.where(models.PlaybookStep.playbook_id == playbook_id)
    q = q.order_by(models.PlaybookStep.number.asc())
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_chain_step(
    db: AsyncSession,
    playbook_id: str,
    number: int,
) -> models.PlaybookStep | None:
    q = await db.execute(
        select(models.PlaybookStep)
        .where(models.PlaybookStep.playbook_id == playbook_id)
        .where(models.PlaybookStep.number == number),
    )
    try:
        return q.scalars().unique().one()
    except exc.NoResultFound:
        return None


async def get_chain_step_by_id(
    db: AsyncSession,
    step_id: str,
) -> models.PlaybookStep | None:
    return await db.get(models.PlaybookStep, step_id)


async def clone_chain_step(
    db: AsyncSession,
    step: models.PlaybookStep,
    playbook_id: str,
    update_label: bool = False,
) -> models.PlaybookStep:
    to_add = schemas.ChainStepCreate(
        playbook_id=playbook_id,
        number=step.number + 1,
        delay=step.delay,
        label=step.label,
        depends_on=step.depends_on,
    )
    if step.proxy_job_id:
        proxy_job = await clone_proxy_job(db, step.proxy_job_id, playbook_id)
        if proxy_job:
            to_add.proxy_job_id = proxy_job.id
    if step.c2_job_id:
        new_job = await clone_c2_job(db, step.c2_job_id, playbook_id)
        if new_job:
            to_add.c2_job_id = new_job.id
    if update_label:
        highest = await get_highest_step(db, step.playbook_id)
        to_add.number = (highest or 0) + 1
        to_add.label = to_excel(to_add.number)
    new_step = await add_step(db, to_add, add_depends_on=False)
    if step.step_modifiers:
        for step_modifier in step.step_modifiers:
            await create_playbook_step_modifier(
                db,
                schemas.PlaybookStepModifierCreate(
                    input_path=step_modifier.input_path,
                    playbook_step_id=new_step.id,
                    output_path=step_modifier.output_path,
                    regex=step_modifier.regex,
                ),
            )
    if playbook_id:
        await send_update_playbook(playbook_id, "new_step", id=str(new_step.id))
    return new_step


async def update_chain_status(
    db: AsyncSession,
    status: str,
    playbook_id: str | UUID4,
    completed: int,
) -> models.Playbook | None:
    from .action import update_action_status

    chain = await db.get(models.Playbook, playbook_id)
    if chain:
        if status == schemas.Status.started:
            chain.time_started = func.now()
        if status == schemas.Status.completed:
            chain.time_completed = func.now()
        chain.status = status
        chain.completed = completed
        db.add(chain)
        await db.commit()
        await db.refresh(chain)
        msg = messages_pb2.Event(event="playbook_status", chain_status=status)
        await redis.publish(f"playbook_stream_{playbook_id}", msg.SerializeToString())
        await update_action_status(db, status, playbook_id)
        return chain
    return None


async def update_step_status(
    db: AsyncSession,
    status: str,
    step_id: str | uuid.UUID,
) -> models.PlaybookStep | None:
    step = await db.get(models.PlaybookStep, step_id)
    if step:
        if status in [
            schemas.Status.started,
            schemas.Status.starting,
            schemas.Status.queued,
            schemas.Status.scheduled,
        ]:
            step.time_started = func.now()
        if status in [schemas.Status.completed, schemas.Status.error]:
            step.time_completed = func.now()
        step.status = status
        db.add(step)
        await db.commit()
        await db.refresh(step)
        msg = messages_pb2.Event(event="step_status", chain_status=status)
        await redis.publish(
            f"playbook_stream_{step.playbook_id}",
            msg.SerializeToString(),
        )
        return step
    return None


async def get_chain_step_by_proxy_job_id(
    db: AsyncSession,
    job_id: str,
) -> models.PlaybookStep | None:
    q = await db.execute(
        select(models.PlaybookStep).where(models.PlaybookStep.proxy_job_id == job_id),
    )
    try:
        return q.scalars().unique().one()
    except exc.NoResultFound:
        return None


async def get_chain_step_by_c2_job_id(
    db: AsyncSession,
    job_id: str | UUID4,
) -> models.PlaybookStep | None:
    q = await db.execute(
        select(models.PlaybookStep).where(models.PlaybookStep.c2_job_id == job_id),
    )
    try:
        return q.scalars().unique().one()
    except exc.NoResultFound:
        return None


async def update_playbook_steps(db: AsyncSession, playbook_id: str | uuid.UUID) -> None:
    playbook = await get_playbook(db, playbook_id)
    if playbook:
        count = 0
        steps = await get_playbook_steps(db, 0, 100000, playbook_id)
        for step in steps:
            count += 1
            step.number = count
            db.add(step)
        await db.execute(
            update(models.Playbook).where(models.Playbook.id == playbook_id).values(steps=count),
        )
        await db.commit()


async def delete_step(db: AsyncSession, step_id: str) -> None:
    db_step = await get_chain_step_by_id(db, step_id)
    if db_step:
        playbook_id = db_step.playbook_id
        await delete_input_files(db, db_step.proxy_job_id, db_step.c2_job_id)
        await db.execute(
            delete(models.PlaybookStep).where(models.PlaybookStep.id == step_id),
        )
        if db_step.proxy_job_id:
            await db.execute(
                delete(models.ProxyJob).where(
                    models.ProxyJob.id == db_step.proxy_job_id,
                ),
            )
        if db_step.c2_job_id:
            await db.execute(
                delete(models.C2Job).where(models.C2Job.id == db_step.c2_job_id),
            )
        await db.commit()
        if playbook_id:
            await update_playbook_steps(db, playbook_id)
            await send_update_playbook(playbook_id, "deleted_step", str(step_id))


async def get_highest_step(db, playbook_id) -> int:
    q = (
        select(models.PlaybookStep.number)
        .where(models.PlaybookStep.playbook_id == playbook_id)
        .order_by(models.PlaybookStep.number.desc())
    )
    result = await db.execute(q.limit(1))
    return result.scalars().first()


async def add_step(
    db: AsyncSession,
    step: schemas.ChainStepCreate,
    add_depends_on: bool | None = True,
) -> models.PlaybookStep:
    if not step.number:
        highest = await get_highest_step(db, step.playbook_id)
        step.number = (highest or 0) + 1
    if not step.label:
        step.label = to_excel(step.number)
    if add_depends_on and (not step.depends_on) and (step.number > 1):
        step.depends_on = to_excel(step.number - 1)
    db_step = models.PlaybookStep(**step.model_dump())
    db_step.status = schemas.Status.created
    db.add(db_step)
    await db.flush()  # Ensure the step is in the transaction before querying
    if step.playbook_id:
        await update_playbook_steps(db, step.playbook_id)
        await db.refresh(db_step)  # Refresh the object after commit
        await send_update_playbook(step.playbook_id, "new_step", str(db_step.id))
    else:
        await db.commit()
        await db.refresh(db_step)

    return db_step


async def update_step(
    db: AsyncSession,
    step_id: str,
    step: schemas.ChainStepCreate,
) -> models.PlaybookStep | None:
    db_step = await get_chain_step_by_id(db, step_id)
    if db_step:
        db_step.number = step.number
        db_step.playbook_id = step.playbook_id
        db_step.proxy_job_id = step.proxy_job_id
        db_step.c2_job_id = step.c2_job_id
        db_step.delay = step.delay
        db_step.execute_after = step.execute_after
        db_step.label = step.label
        db_step.depends_on = step.depends_on
        db.add(db_step)
        await db.commit()
        if step.playbook_id:
            await update_playbook_steps(db, step.playbook_id)
            await send_update_playbook(
                str(step.playbook_id),
                "updated_step",
                str(db_step.id),
            )
        await db.refresh(db_step)
        return db_step
    return None


async def get_playbook_template(
    db: AsyncSession,
    template_id: str | uuid.UUID,
) -> models.PlaybookTemplate | None:
    return await db.get(models.PlaybookTemplate, template_id)


async def get_chain_templates(
    db: AsyncSession,
    filters: filters.PlaybookTemplateFilter,
) -> Iterable[models.PlaybookTemplate]:
    q: Select = select(models.PlaybookTemplate).outerjoin(
        models.PlaybookTemplate.labels,
    )
    q = filters.filter(q)
    with contextlib.suppress(NotImplementedError):
        q = filters.sort(q)
    q = q.group_by(models.PlaybookTemplate.id)
    if filters.search and len(filters.search) == 36:
        q = q.where(
            or_(
                models.PlaybookTemplate.name.ilike(f"%{filters.search}%"),
                models.PlaybookTemplate.id == filters.search,
            ),
        )
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_chain_templates_paged(
    db: AsyncSession,
    filters: filters.PlaybookTemplateFilter,
) -> Page[models.PlaybookTemplate]:
    q: Select = select(models.PlaybookTemplate).outerjoin(
        models.PlaybookTemplate.labels,
    )
    q = filters.filter(q)
    with contextlib.suppress(NotImplementedError):
        q = filters.sort(q)
    q = q.group_by(models.PlaybookTemplate.id)
    if filters.search and len(filters.search) == 36:
        q = q.where(
            or_(
                models.PlaybookTemplate.name.ilike(f"%{filters.search}%"),
                models.PlaybookTemplate.id == filters.search,
            ),
        )
    return await apaginate(db, q)


async def get_playbook_template_filters(
    db: AsyncSession,
    filters: filters.PlaybookTemplateFilter,
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.PlaybookTemplate.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    for name in ["tactic", "technique"]:
        entry = await create_filter_for_column(
            db,
            q,
            getattr(models.PlaybookTemplate, name),
            name,
            name,
        )
        result.append(entry)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


async def create_playbook_template(
    db: AsyncSession,
    playbook_template: schemas.PlaybookTemplateCreate,
) -> models.PlaybookTemplate:
    template = await get_playbook_template(db, playbook_template.id)
    exists = False
    if not template:
        template = models.PlaybookTemplate(
            id=playbook_template.id,
            name=playbook_template.name,
            icon=playbook_template.icon,
            yaml=playbook_template.yaml,
            tactic=playbook_template.tactic,
            technique=playbook_template.technique,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
    else:
        exists = True
        await db.execute(
            update(models.PlaybookTemplate)
            .where(models.PlaybookTemplate.id == playbook_template.id)
            .values(
                yaml=playbook_template.yaml,
                name=playbook_template.name,
                icon=playbook_template.icon,
                tactic=playbook_template.tactic,
                technique=playbook_template.technique,
            ),
        )
        await db.commit()
        template = await db.get(models.PlaybookTemplate, playbook_template.id)
        orm_template_instance = await db.get(
            models.PlaybookTemplate,
            playbook_template.id,
        )
        if orm_template_instance:
            template = orm_template_instance
    if exists:
        await delete_label_item(
            db,
            schemas.LabeledItemDelete(playbook_template_id=playbook_template.id),
        )
    for entry in playbook_template.labels or []:
        label = await get_label_by_name(db, entry)
        if not label:
            label = await create_label(
                db,
                schemas.LabelCreate(name=entry, category="Playbooks"),
            )
        await create_label_item(
            db,
            schemas.LabeledItemCreate(
                label_id=label.id,
                playbook_template_id=playbook_template.id,
            ),
        )
    return template


async def get_playbook_steps_modifiers_paged(
    db: AsyncSession,
    playbook_step_id: UUID4 | str,
) -> Page[models.PlaybookStepModifier]:
    q = select(models.PlaybookStepModifier).order_by(
        models.PlaybookStepModifier.time_created.desc(),
    )
    if playbook_step_id:
        q = q.where(models.PlaybookStepModifier.playbook_step_id == playbook_step_id)
    return await apaginate(db, q)


async def get_playbook_steps_modifiers(
    db: AsyncSession,
    playbook_step_id: UUID4 | str,
) -> Iterable[models.PlaybookStepModifier]:
    q = select(models.PlaybookStepModifier).order_by(
        models.PlaybookStepModifier.time_created.desc(),
    )
    if playbook_step_id:
        q = q.where(models.PlaybookStepModifier.playbook_step_id == playbook_step_id)
    resp = await db.execute(q)
    return resp.scalars().unique().all()


async def create_playbook_step_modifier(
    db: AsyncSession,
    step: schemas.playbook_step.PlaybookStepModifierCreate,
) -> models.PlaybookStepModifier:
    db_step = models.PlaybookStepModifier(**step.model_dump())
    db.add(db_step)
    await db.commit()
    await db.refresh(db_step)
    return db_step


async def get_playbook_step_modifier(
    db: AsyncSession,
    step_id: str | UUID4,
) -> models.PlaybookStepModifier | None:
    return await db.get(models.PlaybookStepModifier, step_id)


async def update_playbook_step_modifier(
    db: AsyncSession,
    step_id: str,
    step: schemas.playbook_step.PlaybookStepModifierCreate,
) -> models.PlaybookStepModifier | None:
    step_db = await get_playbook_step_modifier(db, step_id=step_id)
    if step_db:
        q = (
            update(models.PlaybookStepModifier)
            .where(models.PlaybookStepModifier.id == step_id)
            .values(**step.model_dump())
        )
        await db.execute(q)
        await db.commit()
        await db.refresh(step_db)
        return step_db
    return None


async def delete_playbook_step_modifier(db: AsyncSession, step_id: str | UUID4) -> None:
    step_db = await get_playbook_step_modifier(db, step_id=step_id)
    if step_db:
        await db.execute(
            delete(models.PlaybookStepModifier).where(
                models.PlaybookStepModifier.id == step_id,
            ),
        )
        await db.commit()


async def delete_action_playbook_mapping(
    db: AsyncSession,
    action_id: UUID4 | str,
) -> None:
    q = delete(models.ActionPlaybook).where(
        models.ActionPlaybook.action_id == action_id,
    )
    await db.execute(q)
    await db.commit()


async def add_action_playbook_mapping(
    db: AsyncSession,
    action_id: UUID4 | str,
    playbook_template_id: UUID4 | str,
) -> bool:
    q = insert(models.ActionPlaybook).values(
        action_id=action_id,
        playbook_template_id=playbook_template_id,
    )
    try:
        await db.execute(q)
        await db.commit()
        return True
    except IntegrityError:
        await db.rollback()
        return False


async def get_plan_steps_paged(
    db: AsyncSession,
    filters: filters.PlanStepFilter,
) -> Page[models.PlanStep]:
    q: Select = select(models.PlanStep)
    q = q.outerjoin(models.PlanStep.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.PlanStep.id)
    return await apaginate(db, q)


async def get_plan_steps(
    db: AsyncSession,
    filters: filters.PlanStepFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.PlanStep]:
    q: Select = select(models.PlanStep)
    q = q.outerjoin(models.PlanStep.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_plan_steps_filters(db: AsyncSession, filters: filters.PlanStepFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.PlanStep.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["status"]:
        res = await create_filter_for_column(
            db,
            q,
            getattr(models.PlanStep, field),
            field,
            field,
        )
        result.append(res)
    return result


async def get_plan_step(db: AsyncSession, id: UUID4 | str) -> models.PlanStep | None:
    stmt = select(models.PlanStep).where(models.PlanStep.id == id)
    stmt = stmt.options(
        selectinload(models.PlanStep.suggestions),
    )
    result = await db.execute(stmt)
    return result.scalars().unique().one_or_none()


async def create_plan_step(
    db: AsyncSession,
    plan_step: schemas.PlanStepCreate,
) -> tuple[bool, models.PlanStep]:
    data = plan_step.model_dump()
    q = insert(models.PlanStep).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update("plan_id_order_uc", set_=data)
    result = await db.scalars(
        update_stmt.returning(models.PlanStep),
        execution_options={"populate_existing": True},
    )
    result = result.unique().one()
    created = result.time_updated is None
    await db.refresh(result, ["labels", "suggestions"])
    db.expunge(result)
    await db.commit()
    return (created, result)


async def update_plan_step(
    db: AsyncSession,
    id: str | uuid.UUID,
    plan_step: schemas.PlanStepUpdate,
) -> None:
    q = (
        update(models.PlanStep)
        .where(models.PlanStep.id == id)
        .values(**plan_step.model_dump(exclude_unset=True, exclude_none=True))
    )
    await db.execute(q)
    await db.commit()
    return await get_plan_step(db, id)


async def get_highest_plan_step_order(
    db: AsyncSession,
    plan_id: str | uuid.UUID,
) -> int:
    """Retrieves the highest 'order' number for the steps in a given plan.
    Returns 0 if the plan has no steps.
    """
    q = select(func.max(models.PlanStep.order)).where(
        models.PlanStep.plan_id == plan_id,
    )
    result = await db.execute(q)
    highest_order = result.scalar_one_or_none()
    return highest_order if highest_order is not None else 0
