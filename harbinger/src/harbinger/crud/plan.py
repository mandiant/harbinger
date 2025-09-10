import uuid
from typing import Iterable, Optional, Tuple

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger.database import filters
from harbinger.database.cache import redis_cache_fixed_key
from harbinger.database.database import SessionLocal
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import create_filter_for_column
from .label import get_labels_for_q


@redis_cache_fixed_key(
    cache_key="implant_statistics",
    session_factory=SessionLocal,
    schema=schemas.StatisticsItems,
)
async def get_implant_statistics(db: AsyncSession) -> dict:
    stats = {}
    q = select(models.C2Implant.payload_type, func.count(models.C2Implant.id)).group_by(
        models.C2Implant.payload_type
    )
    results = await db.execute(q)
    for entry in results.all():
        if entry[0]:
            stats[entry[0]] = entry[1]
    return dict(
        items=[
            dict(key=key, value=value, icon="question_mark")
            for key, value in stats.items()
        ]
    )


async def get_plans_paged(
    db: AsyncSession, filters: filters.PlanFilter
) -> Page[models.Plan]:
    q: Select = select(models.Plan)
    q = q.outerjoin(models.Plan.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Plan.id)
    return await paginate(db, q)


async def get_plans(
    db: AsyncSession, filters: filters.PlanFilter, offset: int = 0, limit: int = 10
) -> Iterable[models.Plan]:
    q: Select = select(models.Plan)
    q = q.outerjoin(models.Plan.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_plans_filters(db: AsyncSession, filters: filters.PlanFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Plan.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["status"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Plan, field), field, field
        )
        result.append(res)
    return result


async def get_plan(db: AsyncSession, id: UUID4 | str) -> Optional[models.Plan]:
    return await db.get(models.Plan, id)


async def create_plan(
    db: AsyncSession, plan: schemas.PlanCreate
) -> Tuple[bool, models.Plan]:
    data = plan.model_dump()
    q = insert(models.Plan).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update("plan_name", set_=data)
    result = await db.scalars(
        update_stmt.returning(models.Plan),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    return (result.time_updated == None, result)


async def update_plan(
    db: AsyncSession, id: str | uuid.UUID, plan: schemas.PlanUpdate
) -> None:
    q = (
        update(models.Plan)
        .where(models.Plan.id == id)
        .values(
            **plan.model_dump(
                exclude_unset=True, exclude_defaults=True, exclude_none=True
            )
        )
    )
    await db.execute(q)
    await db.commit()
