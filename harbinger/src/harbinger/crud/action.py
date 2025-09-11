from typing import Optional

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger import filters
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import create_filter_for_column
from .label import (
    create_label,
    create_label_item,
    delete_label_item,
    get_label_by_name,
    get_labels_for_q,
)
from .playbook import add_action_playbook_mapping, delete_action_playbook_mapping


async def update_action_status(
    db: AsyncSession, status: str, playbook_id: str | UUID4
) -> None:
    q = (
        update(models.Action)
        .values(status=status)
        .where(models.Playbook.id == playbook_id)
        .where(
            models.Playbook.playbook_template_id
            == models.ActionPlaybook.playbook_template_id
        )
        .where(models.Action.id == models.ActionPlaybook.action_id)
    )
    if status == schemas.Status.running:
        q = q.values(time_started=func.now())
    if status == schemas.Status.completed:
        q = q.values(time_completed=func.now())
    await db.execute(q)
    await db.commit()


async def get_actions_paged(
    db: AsyncSession, filters: filters.ActionFilter
) -> Page[models.Action]:
    q: Select = select(models.Action)
    q = q.outerjoin(models.Action.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Action.id)
    return await paginate(db, q)


async def get_action_filters(db: AsyncSession, filters: filters.ActionFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Action.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["status"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Action, field), field, field
        )
        result.append(res)
    return result


async def get_action(db: AsyncSession, id: UUID4) -> Optional[models.Action]:
    return await db.get(models.Action, id)


async def create_action(db: AsyncSession, action: schemas.ActionCreate) -> None:
    q = (
        insert(models.Action)
        .values(**action.model_dump(exclude={"labels", "playbook_template_ids"}))
        .values(time_created=func.now())
    )
    q = q.on_conflict_do_update(
        models.Action.__table__.primary_key,
        set_=dict(
            name=action.name, description=action.description, time_updated=func.now()
        ),
    )
    result: models.Action = await db.scalars(
        q.returning(models.Action), execution_options={"populate_existing": True}
    )
    await db.commit()
    await delete_label_item(db, schemas.LabeledItemDelete(action_id=action.id))
    for entry in action.labels or []:
        label = await get_label_by_name(db, entry)
        if not label:
            label = await create_label(
                db, schemas.LabelCreate(name=entry, category="Playbooks")
            )
        await create_label_item(
            db, schemas.LabeledItemCreate(label_id=label.id, action_id=action.id)
        )
    await delete_action_playbook_mapping(db, action.id)
    for template_id in action.playbook_template_ids or []:
        added = await add_action_playbook_mapping(
            db, action_id=action.id, playbook_template_id=template_id
        )
    await db.commit()
