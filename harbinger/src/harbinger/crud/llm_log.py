import uuid
from typing import Iterable, Optional

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger import filters
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import create_filter_for_column
from .label import get_labels_for_q


async def get_llm_logs_paged(
    db: AsyncSession, filters: filters.LlmLogFilter
) -> Page[models.LlmLog]:
    q: Select = select(models.LlmLog)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.LlmLog.id)
    return await paginate(db, q)


async def get_llm_logs(
    db: AsyncSession, filters: filters.LlmLogFilter, offset: int = 0, limit: int = 10
) -> Iterable[models.LlmLog]:
    q: Select = select(models.LlmLog)
    q = q.outerjoin(models.LlmLog.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_llm_logs_filters(db: AsyncSession, filters: filters.LlmLogFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.LlmLog.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["log_type"]:
        res = await create_filter_for_column(
            db, q, getattr(models.LlmLog, field), field, field
        )
        result.append(res)
    return result


async def get_llm_log(db: AsyncSession, id: UUID4) -> Optional[models.LlmLog]:
    """Retrieves a single LLM log entry by its ID."""
    return await db.get(models.LlmLog, id)


async def create_llm_log(
    db: AsyncSession, llm_log: schemas.LlmLogCreate
) -> models.LlmLog:
    """Creates a new LLM log entry in the database with a direct insert."""
    db_log = models.LlmLog(**llm_log.model_dump())
    db.add(db_log)
    await db.commit()
    await db.refresh(db_log)
    return db_log


async def update_llm_log(
    db: AsyncSession, id: str | uuid.UUID, llm_logs: schemas.LlmLogUpdate
) -> None:
    q = (
        update(models.LlmLog)
        .where(models.LlmLog.id == id)
        .values(
            **llm_logs.model_dump(
                exclude_unset=True, exclude_defaults=True, exclude_none=True
            )
        )
    )
    await db.execute(q)
    await db.commit()
