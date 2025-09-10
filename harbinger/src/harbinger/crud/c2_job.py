from typing import Any, Iterable, Optional

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger.database import filters
from harbinger.database.cache import redis_cache, redis_cache_invalidate
from harbinger.database.database import SessionLocal
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import DEFAULT_CACHE_TTL, create_filter_for_column
from .file import create_input_file
from .label import get_labels_for_q


async def clone_c2_job(
    db: AsyncSession, c2_job_id: str, playbook_id: str | None = None
) -> models.C2Job | None:
    c2_job = await db.get(models.C2Job, c2_job_id)
    if c2_job:
        new_c2_job = await create_c2_job(
            db,
            schemas.C2JobCreate(
                command=c2_job.command,
                arguments=c2_job.arguments,
                c2_implant_id=c2_job.c2_implant_id,
                input_files=[str(file.id) for file in c2_job.input_files],
                add_labels=list(c2_job.add_labels or []),
                playbook_id=playbook_id,
            ),
        )
        return new_c2_job


async def get_c2_jobs_paged(
    db: AsyncSession, filters: filters.C2JobFilter
) -> Page[models.C2Job]:
    q: Select = select(models.C2Job)
    q = q.outerjoin(models.C2Job.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.C2Job.id)
    return await paginate(db, q)


async def get_c2_jobs_filters(db: AsyncSession, filters: filters.C2JobFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.C2Job.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["status", "command", "arguments"]:
        res = await create_filter_for_column(
            db, q, getattr(models.C2Job, field), field, field
        )
        result.append(res)
    return result


async def get_c2_jobs(
    db: AsyncSession, completed_only: bool = False
) -> Iterable[models.C2Job]:
    q = select(models.C2Job)
    if completed_only:
        q = q.where(models.C2Job.time_completed.isnot(None)).order_by(
            models.C2Job.time_completed.asc()
        )
    result = await db.execute(q)
    return result.scalars().unique().all()


async def create_c2_job(db: AsyncSession, job: schemas.C2JobCreate) -> models.C2Job:
    entries: dict[str, Any] = job.model_dump()
    input_files = entries.pop("input_files")
    db_obj = models.C2Job(**entries)
    db_obj.status = schemas.Status.created
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    for input_file in input_files or []:
        await create_input_file(db, input_file, c2_job_id=str(db_obj.id))
    return db_obj


@redis_cache(
    key_prefix="c2_job",
    session_factory=SessionLocal,
    schema=schemas.C2Job,
    key_param_name="job_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_c2_job(db: AsyncSession, job_id: str | UUID4) -> Optional[models.C2Job]:
    return await db.get(models.C2Job, job_id)


@redis_cache_invalidate(key_prefix="c2_job", key_param_name="c2_job_id")
async def update_c2_job(
    db: AsyncSession, c2_job_id: str | UUID4, job: schemas.C2JobCreate
) -> Optional[models.C2Job]:
    from .playbook import send_update_playbook

    values = job.model_dump()
    input_files = values.pop("input_files")
    q = update(models.C2Job).where(models.C2Job.id == c2_job_id).values(**values)
    await db.execute(q)
    await db.commit()
    await delete_input_files(db, c2_job_id=c2_job_id)
    for input_file in input_files:
        await create_input_file(db, input_file, c2_job_id=c2_job_id)
    c2_job = await db.get(models.C2Job, c2_job_id)
    if c2_job and c2_job.playbook_id:
        await send_update_playbook(c2_job.playbook_id, "updated_c2_job", str(c2_job_id))
    return c2_job


@redis_cache_invalidate(key_prefix="c2_job", key_param_name="c2_job_id")
async def update_c2_job_status(
    db: AsyncSession, c2_job_id: str | UUID4, status: str, message: str = ""
) -> None:
    values = dict(status=status)
    if message:
        values["message"] = message
    if status == schemas.Status.running:
        values["time_started"] = func.now()
    if status == schemas.Status.completed or status == schemas.Status.error:
        values["time_completed"] = func.now()
    q = update(models.C2Job).where(models.C2Job.id == c2_job_id).values(**values)
    await db.execute(q)
    await db.commit()


async def get_c2_job_status_by_task(
    db: AsyncSession, c2_task_id: str | UUID4 | None = None
) -> Optional[models.C2Job]:
    q = select(models.C2Job)
    if c2_task_id:
        q = q.where(models.C2Job.c2_task_id == c2_task_id)
    result = await db.execute(q)
    return result.unique().scalar_one_or_none()


async def update_c2_job_c2_task_id(
    db: AsyncSession, c2_job_id: UUID4 | str, c2_task_id: UUID4 | str
) -> None:
    q = (
        update(models.C2Job)
        .where(models.C2Job.id == c2_job_id)
        .values(c2_task_id=c2_task_id)
    )
    await db.execute(q)
    await db.commit()
