from typing import Optional

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger import filters
from harbinger.database.cache import redis_cache
from harbinger.database.database import SessionLocal
from pydantic import UUID4
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import DEFAULT_CACHE_TTL
from .label import get_labels_for_q


async def get_c2_output_paged(
    db: AsyncSession, filters: filters.C2OutputFilter, c2_job_id: str | None = None
) -> Page[models.C2Output]:
    q: Select = (
        select(models.C2Output)
        .outerjoin(models.C2Output.labels)
        .group_by(models.C2Output.id)
    )
    q = filters.filter(q)
    if c2_job_id:
        q = q.where(models.C2Job.id == c2_job_id)
        q = q.where(models.C2Job.c2_task_id == models.C2Output.c2_task_id)
    q = filters.sort(q)
    return await paginate(db, q)


async def get_c2_output_filters(
    db: AsyncSession, filters: filters.C2OutputFilter
) -> list[schemas.Filter]:
    q: Select = (
        select(func.count(models.C2Output.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    result: list[schemas.Filter] = []
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


@redis_cache(
    key_prefix="c2_output",
    session_factory=SessionLocal,
    schema=schemas.C2Output,
    key_param_name="c2_output_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_c2_output(
    db: AsyncSession, c2_output_id: str | UUID4
) -> Optional[models.C2Output]:
    return await db.get(models.C2Output, c2_output_id)
