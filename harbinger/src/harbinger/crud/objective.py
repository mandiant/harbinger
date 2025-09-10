import uuid
from typing import Iterable, Optional, Tuple

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger.database import filters
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import create_filter_for_column
from .label import get_labels_for_q


async def get_objectives_paged(
    db: AsyncSession, filters: filters.ObjectivesFilter
) -> Page[models.Objectives]:
    q: Select = select(models.Objectives)
    q = q.outerjoin(models.Objectives.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Objectives.id)
    return await paginate(db, q)


async def get_objectives(
    db: AsyncSession,
    filters: filters.ObjectivesFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Objectives]:
    q: Select = select(models.Objectives)
    q = q.outerjoin(models.Objectives.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_objectives_filters(db: AsyncSession, filters: filters.ObjectivesFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Objectives.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["status"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Objectives, field), field, field
        )
        result.append(res)
    return result


async def get_objective(db: AsyncSession, id: UUID4) -> Optional[models.Objectives]:
    return await db.get(models.Objectives, id)


async def create_objective(
    db: AsyncSession, objective: schemas.ObjectiveCreate
) -> Tuple[bool, models.Objectives]:
    data = objective.model_dump()
    q = insert(models.Objectives).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update(
        models.Objectives.__table__.primary_key, set_=data
    )
    result = await db.scalars(
        update_stmt.returning(models.Objectives),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    return (result.time_updated == None, result)


async def update_objective(
    db: AsyncSession, id: str | uuid.UUID, objective: schemas.ObjectiveCreate
) -> None:
    q = (
        update(models.Objectives)
        .where(models.Objectives.id == id)
        .values(**objective.model_dump())
    )
    await db.execute(q)
    await db.commit()
