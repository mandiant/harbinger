import uuid
from typing import Iterable, Union

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger import filters
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import func

from ._common import create_filter_for_column


async def get_manual_timeline_tasks(
    db: AsyncSession, processing_status: str
) -> Iterable[models.ManualTimelineTask]:
    q = select(models.ManualTimelineTask)
    q = q.where(models.ManualTimelineTask.processing_status == processing_status)
    q = q.order_by(models.ManualTimelineTask.time_completed.asc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def update_manual_timeline_summary(
    db, manuel_task_id: str | UUID4, summary: str, status: str
) -> None:
    q = (
        update(models.ManualTimelineTask)
        .where(models.ManualTimelineTask.id == manuel_task_id)
        .values(processing_status=status, ai_summary=summary)
    )
    await db.execute(q)
    await db.commit()


async def get_timeline_paged(
    db: AsyncSession, filters: filters.TimeLineFilter
) -> Page[Union[models.C2Task, models.ProxyJob, models.ManualTimelineTask]]:
    q: Select = select(models.TimeLine)
    q = filters.filter(q)
    q = filters.sort(q)
    return await paginate(db, q)


async def get_timeline_filters(db: AsyncSession, filters: filters.TimeLineFilter):
    result: list[schemas.Filter] = []
    q: Select = select(func.count(models.TimeLine.id.distinct()).label("count_1"))
    q = filters.filter(q)
    for field in ["status"]:
        res = await create_filter_for_column(
            db, q, getattr(models.TimeLine, field), field, field
        )
        result.append(res)
    return result


async def get_timeline(
    db: AsyncSession, status: list[str]
) -> Iterable[Union[models.C2Task, models.ProxyJob]]:
    q = select(models.TimeLine).options(joinedload("*"))
    if status:
        q = q.where(models.TimeLine.status.in_(status))
    q = q.order_by(models.TimeLine.time_completed.asc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def create_manual_timeline_task(
    db: AsyncSession, manual_timeline_tasks: schemas.ManualTimelineTaskCreate
) -> models.ManualTimelineTask:
    result = models.ManualTimelineTask(**manual_timeline_tasks.model_dump())
    db.add(result)
    await db.commit()
    await db.refresh(result)
    return result


async def update_manual_timeline_task(
    db: AsyncSession,
    id: str | uuid.UUID,
    manual_timeline_tasks: schemas.ManualTimelineTaskCreate,
) -> None:
    q = (
        update(models.ManualTimelineTask)
        .where(models.ManualTimelineTask.id == id)
        .values(**manual_timeline_tasks.model_dump())
    )
    await db.execute(q)
    await db.commit()
