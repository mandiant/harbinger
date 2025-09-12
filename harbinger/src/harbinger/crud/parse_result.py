from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import models, schemas
from harbinger.database.cache import redis_cache
from harbinger.database.database import SessionLocal

from ._common import DEFAULT_CACHE_TTL


async def create_parse_result(
    db: AsyncSession,
    result: schemas.ParseResultCreate,
) -> models.ParseResult:
    result_db = models.ParseResult(**result.model_dump())
    db.add(result_db)
    await db.commit()
    await db.refresh(result_db)
    return result_db


@redis_cache(
    key_prefix="parse_result",
    session_factory=SessionLocal,
    schema=schemas.ParseResult,
    key_param_name="result_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_parse_result(
    db: AsyncSession,
    result_id: UUID4 | str,
) -> models.ParseResult | None:
    return await db.get(models.ParseResult, result_id)


async def get_parse_results_paged(
    db: AsyncSession,
    file_id: str | UUID4 | None = None,
    c2_task_id: str | UUID4 | None = None,
    c2_task_output_id: str | UUID4 | None = None,
    proxy_job_output_id: str | UUID4 | None = None,
    proxy_job_id: str | UUID4 | None = None,
) -> Page[models.ParseResult]:
    q = select(models.ParseResult)
    if file_id:
        q = q.where(models.ParseResult.file_id == file_id)
    if c2_task_id:
        q = q.where(models.ParseResult.c2_task_id == c2_task_id)
    if c2_task_output_id:
        q = q.where(models.ParseResult.c2_task_output_id == c2_task_output_id)
    if proxy_job_output_id:
        q = q.where(models.ParseResult.proxy_job_output_id == proxy_job_output_id)
    if proxy_job_id:
        q = q.where(models.ParseResult.proxy_job_id == proxy_job_id)
    q = q.order_by(models.ParseResult.time_created.asc())
    return await paginate(db, q)
