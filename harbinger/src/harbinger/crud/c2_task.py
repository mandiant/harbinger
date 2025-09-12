import contextlib
from collections.abc import Iterable

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas
from harbinger.database.cache import invalidate_cache_entry, redis_cache
from harbinger.database.database import SessionLocal

from ._common import DEFAULT_CACHE_TTL, create_filter_for_column
from .label import get_labels_for_q


async def get_c2_tasks_paged(
    db: AsyncSession,
    filters: filters.C2TaskFilter,
) -> Page[models.C2Task]:
    q: Select = select(models.C2Task).outerjoin(models.C2Task.labels).group_by(models.C2Task.id)
    q = filters.filter(q)
    with contextlib.suppress(NotImplementedError):
        q = filters.sort(q)
    return await paginate(db, q)


async def get_c2_task_filters(
    db: AsyncSession,
    filters: filters.C2TaskFilter,
) -> list[schemas.Filter]:
    q: Select = (
        select(func.count(models.C2Task.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    result: list[schemas.Filter] = []
    for column in ["status", "command_name", "operator"]:
        ft_entry = await create_filter_for_column(
            db,
            q,
            getattr(models.C2Task, column),
            column,
            column,
        )
        result.append(ft_entry)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


async def get_c2_tasks(
    db: AsyncSession,
    filters: filters.C2TaskFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.C2Task]:
    q: Select = select(models.C2Task).outerjoin(models.C2Task.labels).group_by(models.C2Task.id)
    q = filters.filter(q)
    q = q.offset(offset).limit(limit)
    q = q.order_by(models.C2Task.time_created.desc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def create_or_update_c2_task(
    db: AsyncSession,
    task: schemas.C2TaskCreate,
) -> tuple[bool, models.C2Task]:
    """Creates the c2 task in the database, if the c2 task with that id already exists, updates it.
    returns tuple[bool, C2Task]
    The bool indicates if the task was created.
    """
    q = (
        select(models.C2Task)
        .where(models.C2Task.c2_server_id == task.c2_server_id)
        .where(models.C2Task.internal_id == task.internal_id)
    )
    res = await db.execute(q)
    db_task = res.scalars().first()
    data = task.model_dump()
    data.pop("internal_implant_id", None)
    if db_task:
        new = False
        q = update(models.C2Task).where(models.C2Task.id == db_task.id)
        q = q.values(**data)
        await db.execute(q)
        await db.commit()
        await invalidate_cache_entry("c2_task", db_task.id)
    else:
        db_task = models.C2Task(**data)
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        new = True
    return (new, db_task)


async def create_c2_task_output(
    db: AsyncSession,
    c2_outputs: schemas.C2OutputCreate,
) -> tuple[bool, models.C2Output]:
    data = c2_outputs.model_dump()
    data.pop("internal_task_id", None)
    data.pop("processes", [])
    data.pop("files", [])
    data.pop("bucket", "")
    data.pop("path", "")
    data.pop("file_list", "")
    q = insert(models.C2Output).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update("c2_output_uc", set_=data)
    result = await db.scalars(
        update_stmt.returning(models.C2Output),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    return (result.time_updated is None, result)


@redis_cache(
    key_prefix="c2_task",
    session_factory=SessionLocal,
    schema=schemas.C2Task,
    key_param_name="c2_task_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_c2_task(db, c2_task_id: str | UUID4) -> models.C2Task | None:
    return await db.get(models.C2Task, c2_task_id)


async def get_c2_task_by_internal_id(
    db,
    internal_id: str,
    c2_server_id: str | UUID4,
) -> models.C2Task | None:
    q = (
        select(models.C2Task)
        .where(models.C2Task.internal_id == internal_id)
        .where(models.C2Task.c2_server_id == c2_server_id)
        .limit(1)
    )
    result = await db.execute(q)
    return result.unique().scalar_one_or_none()


async def get_c2_task_output(
    db,
    filters: filters.C2OutputFilter,
    c2_job_id: str | UUID4 = "",
) -> Iterable[models.C2Output]:
    q: Select = select(models.C2Output).outerjoin(models.C2Output.labels).group_by(models.C2Output.id)
    q = filters.filter(q)
    if c2_job_id:
        q = q.where(models.C2Job.id == c2_job_id)
        q = q.where(models.C2Job.c2_task_id == models.C2Output.c2_task_id)
    q = filters.sort(q)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def update_c2_task_summary(
    db,
    c2_task_id: str | UUID4,
    summary: str,
    status: str,
) -> None:
    q = update(models.C2Task).where(models.C2Task.id == c2_task_id).values(processing_status=status, ai_summary=summary)
    await db.execute(q)
    await db.commit()
    await invalidate_cache_entry("c2_task", c2_task_id)
