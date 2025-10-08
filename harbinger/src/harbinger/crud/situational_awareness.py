from collections.abc import Iterable

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from pydantic import UUID4
from sqlalchemy import Select, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas

from ._common import create_filter_for_column


async def list_situational_awareness(
    db,
    name: str = "",
    category: str = "",
    domain_id: str | UUID4 = "",
    limit: int = 10,
    offset: int = 0,
) -> Iterable[models.SituationalAwareness]:
    q = select(models.SituationalAwareness)
    if name:
        q = q.where(models.SituationalAwareness.name == name)
    if category:
        q = q.where(models.SituationalAwareness.category == category)
    if domain_id:
        q = q.where(models.SituationalAwareness.domain_id == domain_id)
    q = q.limit(limit).offset(offset)
    q = q.order_by(models.SituationalAwareness.time_created.desc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def list_situational_awarenesss_paged(
    db: AsyncSession,
    filters: filters.SituationalAwarenessFilter,
) -> Page[models.SituationalAwareness]:
    q: Select = select(models.SituationalAwareness)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.SituationalAwareness.id)
    return await apaginate(db, q)


async def get_situational_awarenesss_filters(
    db: AsyncSession,
    filters: filters.SituationalAwarenessFilter,
):
    result: list[schemas.Filter] = []
    q: Select = select(
        func.count(models.SituationalAwareness.id.distinct()).label("count_1"),
    )
    q = filters.filter(q)
    for field in ["name", "category"]:
        res = await create_filter_for_column(
            db,
            q,
            getattr(models.SituationalAwareness, field),
            field,
            field,
        )
        result.append(res)
    return result


async def get_situational_awareness(
    db,
    sa_id: str | UUID4,
) -> models.SituationalAwareness | None:
    return await db.get(models.SituationalAwareness, sa_id)


async def update_situational_awareness(
    db,
    sa_id: str | UUID4,
    sa: schemas.SituationalAwarenessCreate,
):
    q = update(models.SituationalAwareness).where(models.SituationalAwareness.id == sa_id).values(**sa.model_dump())
    await db.execute(q)
    await db.commit()


async def delete_situational_awareness(db, sa_id: str | UUID4):
    q = q = delete(models.SituationalAwareness).where(
        models.SituationalAwareness.id == sa_id,
    )
    await db.execute(q)
    await db.commit()


async def get_or_create_situational_awareness(
    db,
    sa: schemas.SituationalAwarenessCreate,
) -> tuple[bool, models.SituationalAwareness]:
    created = False
    q = (
        select(models.SituationalAwareness)
        .where(models.SituationalAwareness.name == sa.name)
        .where(models.SituationalAwareness.category == sa.category)
    )
    if sa.value_string is not None:
        q = q.where(models.SituationalAwareness.value_string == sa.value_string)
    if sa.value_bool is not None:
        q = q.where(models.SituationalAwareness.value_bool == sa.value_bool)
    if sa.value_int is not None:
        q = q.where(models.SituationalAwareness.value_int == sa.value_int)
    if sa.value_json is not None:
        q = q.where(models.SituationalAwareness.value_json == sa.value_json)
    q = await db.execute(q)
    sa_db = q.scalars().unique().first()
    if not sa_db:
        created = True
        sa_db = models.SituationalAwareness(**sa.model_dump())
        db.add(sa_db)
        await db.commit()
        await db.refresh(sa_db)
    return (created, sa_db)


async def get_sa_statistics(db: AsyncSession) -> dict:
    stats = {}
    q = select(
        models.SituationalAwareness.category,
        func.count(models.SituationalAwareness.id),
    ).group_by(models.SituationalAwareness.category)
    result = await db.execute(q)
    for entry in result.all():
        if entry[0]:
            stats[entry[0]] = entry[1]
    return {"items": [{"key": key, "value": value} for key, value in stats.items()]}
