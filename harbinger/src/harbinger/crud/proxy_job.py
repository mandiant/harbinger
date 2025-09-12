import contextlib
import uuid
from collections.abc import Iterable
from typing import Any

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas
from harbinger.database.cache import redis_cache, redis_cache_invalidate
from harbinger.database.database import SessionLocal

from ._common import DEFAULT_CACHE_TTL
from .file import create_input_file, delete_input_files


@redis_cache(
    key_prefix="proxy_job",
    session_factory=SessionLocal,
    schema=schemas.ProxyJob,
    key_param_name="job_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_proxy_job(
    db: AsyncSession,
    job_id: str | UUID4,
) -> models.ProxyJob | None:
    return await db.get(models.ProxyJob, job_id)


@redis_cache_invalidate(key_prefix="proxy_job", key_param_name="job_id")
async def update_proxy_job(
    db: AsyncSession,
    job_id: str | UUID4,
    job: schemas.ProxyJobCreate,
) -> models.ProxyJob | None:
    from .playbook import send_update_playbook

    values = job.model_dump()
    input_files = values.pop("input_files")
    q = update(models.ProxyJob).where(models.ProxyJob.id == job_id).values(**values)
    await db.execute(q)
    await db.commit()
    await delete_input_files(db, proxy_job_id=job_id)
    for input_file in input_files:
        await create_input_file(db, input_file, proxy_job_id=job_id)
    proxy_job = await db.get(models.ProxyJob, job_id)
    if proxy_job and proxy_job.playbook_id:
        await send_update_playbook(
            proxy_job.playbook_id,
            "updated_proxy_job",
            str(proxy_job.id),
        )
    return proxy_job


@redis_cache_invalidate(key_prefix="proxy_job", key_param_name="job_id")
async def update_proxy_job_status(
    db: AsyncSession,
    status: str | None,
    job_id: str | UUID4,
    exit_code: int = 0,
) -> models.ProxyJob | None:
    job = await db.get(models.ProxyJob, job_id)
    if job:
        if status == schemas.Status.started:
            job.time_started = func.now()
        if status == schemas.Status.completed:
            job.time_completed = func.now()
        job.status = status or ""
        job.exit_code = exit_code
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job
    return None


async def get_proxy_jobs_paged(
    db: AsyncSession,
    filters: filters.SocksJobFilter,
) -> Page[models.ProxyJob]:
    q: Select = select(models.ProxyJob)
    q = q.outerjoin(models.ProxyJob.labels)
    q = filters.filter(q)
    with contextlib.suppress(NotImplementedError):
        q = filters.sort(q)
    q = q.group_by(models.ProxyJob.id)
    return await paginate(db, q)


async def get_proxy_jobs(
    db: AsyncSession,
    filters: filters.SocksJobFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.ProxyJob]:
    q: Select = select(models.ProxyJob).outerjoin(models.ProxyJob.labels).group_by(models.ProxyJob.id)
    q = filters.filter(q)
    q = q.offset(offset).limit(limit)
    q = q.order_by(models.ProxyJob.time_created.desc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def create_proxy_job(
    db: AsyncSession,
    proxy_job: schemas.ProxyJobCreate,
) -> models.ProxyJob:
    entries: dict[str, Any] = proxy_job.model_dump()
    input_files = entries.pop("input_files")
    db_proxy_job = models.ProxyJob(**entries)
    db_proxy_job.status = schemas.Status.created
    db.add(db_proxy_job)
    await db.commit()
    for input_file in input_files:
        await create_input_file(db, input_file, proxy_job_id=str(db_proxy_job.id))
    await db.refresh(db_proxy_job)
    return db_proxy_job


async def create_proxy_job_output(
    db: AsyncSession,
    output: schemas.ProxyJobOutputCreate,
) -> None:
    proxy_job_output = models.ProxyJobOutput()
    proxy_job_output.output = output.output
    proxy_job_output.job_id = output.job_id
    db.add(proxy_job_output)
    await db.commit()


async def get_proxy_job_output_paged(
    db: AsyncSession,
    job_id: str = "",
    type: str = "",
) -> Page[models.ProxyJobOutput]:
    q = select(models.ProxyJobOutput)
    if job_id:
        q = q.where(models.ProxyJobOutput.job_id == job_id)
    if type:
        q = q.where(models.ProxyJobOutput.output_type == type)
    return await paginate(db, q.order_by(models.ProxyJobOutput.created_at.asc()))


async def get_proxy_job_output(
    db: AsyncSession,
    job_id: str | uuid.UUID = "",
    type: str = "",
) -> Iterable[models.ProxyJobOutput]:
    q = select(models.ProxyJobOutput)
    if job_id:
        q = q.where(models.ProxyJobOutput.job_id == job_id)
    if type:
        q = q.where(models.ProxyJobOutput.output_type == type)
    q = q.order_by(models.ProxyJobOutput.created_at.asc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def clone_proxy_job(
    db: AsyncSession,
    proxy_job_id: str,
    playbook_id: str | None = None,
) -> models.ProxyJob | None:
    proxy_job = await db.get(models.ProxyJob, proxy_job_id)
    if proxy_job:
        return await create_proxy_job(
            db,
            schemas.ProxyJobCreate(
                credential_id=proxy_job.credential_id,
                command=proxy_job.command,
                proxy_id=proxy_job.proxy_id,
                arguments=proxy_job.arguments,
                input_files=[str(file.id) for file in proxy_job.input_files],
                playbook_id=playbook_id,
                asciinema=proxy_job.asciinema,
                tmate=proxy_job.tmate,
                proxychains=proxy_job.proxychains,
                env=proxy_job.env,
                socks_server_id=proxy_job.socks_server_id,
            ),
        )
    return None
