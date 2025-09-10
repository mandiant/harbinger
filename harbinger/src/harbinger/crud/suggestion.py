import uuid
from typing import Iterable, Optional, Tuple

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger.database import filters
from harbinger.database.cache import redis_cache
from harbinger.database.database import SessionLocal
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import DEFAULT_CACHE_TTL, create_filter_for_column
from .label import get_labels_for_q


async def get_suggestions_paged(
    db: AsyncSession, filters: filters.SuggestionFilter
) -> Page[models.Suggestion]:
    q: Select = select(models.Suggestion)
    q = q.outerjoin(models.Suggestion.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Suggestion.id)
    return await paginate(db, q)


async def get_suggestions(
    db: AsyncSession,
    filters: filters.SuggestionFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Suggestion]:
    q: Select = select(models.Suggestion)
    if filters.plan_step:
        q = q.join(models.Suggestion.plan_step)
    q = q.outerjoin(models.Suggestion.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_suggestions_filters(db: AsyncSession, filters: filters.SuggestionFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Suggestion.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["name"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Suggestion, field), field, field
        )
        result.append(res)
    return result


@redis_cache(
    key_prefix="suggestion",
    session_factory=SessionLocal,
    schema=schemas.Suggestion,
    key_param_name="id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_suggestion(
    db: AsyncSession, id: UUID4 | str
) -> Optional[models.Suggestion]:
    return await db.get(models.Suggestion, id)


async def create_suggestion(
    db: AsyncSession, suggestion: schemas.SuggestionCreate
) -> Tuple[bool, models.Suggestion]:
    """
    Creates a new suggestion in the database.
    """
    db_suggestion = models.Suggestion(**suggestion.model_dump())
    db.add(db_suggestion)
    await db.commit()
    await db.refresh(db_suggestion)
    return (True, db_suggestion)


async def update_suggestion(
    db: AsyncSession, id: str | uuid.UUID, suggestions: schemas.SuggestionCreate
) -> None:
    q = (
        update(models.Suggestion)
        .where(models.Suggestion.id == id)
        .values(**suggestions.model_dump())
    )
    await db.execute(q)
    await db.commit()


async def delete_suggestion(db: AsyncSession, id: str | uuid.UUID) -> None:
    """
    Disassociates a suggestion from a plan step by setting its plan_step_id to NULL.
    This effectively "archives" the suggestion without deleting it.
    """
    q = (
        update(models.Suggestion)
        .where(models.Suggestion.id == id)
        .values(plan_step_id=None)
    )
    await db.execute(q)
    await db.commit()
