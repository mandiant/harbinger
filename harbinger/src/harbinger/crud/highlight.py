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

from ._common import DEFAULT_CACHE_TTL, create_filter_for_column
from .label import get_labels_for_q


async def create_highlight(
    db: AsyncSession, highlight: schemas.HighlightCreate
) -> models.Highlight:
    result = models.Highlight(**highlight.model_dump())
    db.add(result)
    await db.commit()
    await db.refresh(result)
    return result


@redis_cache(
    key_prefix="highlight",
    session_factory=SessionLocal,
    schema=schemas.Highlight,
    key_param_name="highlight_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_highlight(
    db: AsyncSession, highlight_id: UUID4 | str
) -> Optional[models.Highlight]:
    return await db.get(models.Highlight, highlight_id)


async def get_highlights_paged(
    db: AsyncSession, filters: filters.HighlightFilter
) -> Page[models.Highlight]:
    q: Select = select(models.Highlight)
    q = q.outerjoin(models.Highlight.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Highlight.id)
    return await paginate(db, q)


async def get_highlights_filters(
    db: AsyncSession, filters: filters.HighlightFilter
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Highlight.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["rule_type", "hit"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Highlight, field), field, field
        )
        result.append(res)
    return result
