import uuid
from typing import Iterable, Optional, Tuple

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger import filters
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import create_filter_for_column
from .label import get_labels_for_q


async def get_checklists_paged(
    db: AsyncSession, filters: filters.ChecklistFilter
) -> Page[models.Checklist]:
    q: Select = select(models.Checklist)
    q = q.outerjoin(models.Checklist.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Checklist.id)
    return await paginate(db, q)


async def get_checklists(
    db: AsyncSession, filters: filters.ChecklistFilter, offset: int = 0, limit: int = 10
) -> Iterable[models.Checklist]:
    q: Select = select(models.Checklist)
    q = q.outerjoin(models.Checklist.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_checklists_filters(db: AsyncSession, filters: filters.ChecklistFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Checklist.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["phase", "name", "status"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Checklist, field), field, field
        )
        result.append(res)
    return result


async def get_checklist(db: AsyncSession, id: UUID4) -> Optional[models.Checklist]:
    return await db.get(models.Checklist, id)


async def create_checklist(
    db: AsyncSession, checklists: schemas.ChecklistCreate
) -> Tuple[bool, models.Checklist]:
    data = checklists.model_dump()
    q = insert(models.Checklist).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    if checklists.c2_implant_id:
        update_stmt = q.on_conflict_do_update("checklist_implant_phase_name", set_=data)
    else:
        update_stmt = q.on_conflict_do_update("checklist_domain_phase_name", set_=data)
    result = await db.scalars(
        update_stmt.returning(models.Checklist),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    return (result.time_updated == None, result)


async def update_checklist(
    db: AsyncSession, id: str | uuid.UUID, checklists: schemas.ChecklistCreate
) -> None:
    q = (
        update(models.Checklist)
        .where(models.Checklist.id == id)
        .values(**checklists.model_dump())
    )
    await db.execute(q)
    await db.commit()
