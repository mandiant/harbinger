import contextlib
import uuid
from collections.abc import Iterable
from datetime import datetime

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas
from harbinger.database.cache import (
    invalidate_cache_entry,
    redis_cache,
    redis_cache_invalidate,
)
from harbinger.database.database import SessionLocal

from ._common import DEFAULT_CACHE_TTL, create_filter_for_column
from .label import get_labels_for_q


async def get_c2_implants_paged(
    db: AsyncSession,
    filters: filters.ImplantFilter,
    alive_only: bool = False,
) -> Page[models.C2Implant]:
    q: Select = select(models.C2Implant)
    q = q.outerjoin(models.C2Implant.labels)
    q = filters.filter(q)
    if alive_only:
        q1 = select(models.LabeledItem.c2_implant_id)
        q1 = q1.where(
            models.LabeledItem.label_id == "d734d03b-50d4-43e3-bb0e-e6bf56ec76b1",
        )
        q = q.where(models.C2Implant.id.not_in(q1))
    with contextlib.suppress(NotImplementedError):
        q = filters.sort(q)
    return await paginate(db, q)


async def get_c2_implant_filters(
    db: AsyncSession,
    filters: filters.ImplantFilter,
    alive_only: bool = False,
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.C2Implant.id).distinct().label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    if alive_only:
        q1 = select(models.LabeledItem.c2_implant_id)
        q1 = q1.where(
            models.LabeledItem.label_id == "d734d03b-50d4-43e3-bb0e-e6bf56ec76b1",
        )
        q = q.where(models.C2Implant.id.not_in(q1))
    for entry in ["os", "payload_type", "c2_type", "username", "domain"]:
        ft_entry = await create_filter_for_column(
            db,
            q,
            getattr(models.C2Implant, entry),
            entry,
            entry,
        )
        result.append(ft_entry)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    result.append(
        schemas.Filter(
            name="alive_only",
            multiple=False,
            icon="",
            query_name="alive_only",
            type="bool",
        ),
    )
    return result


async def get_c2_implants(
    db: AsyncSession,
    c2_server_id: str = "",
    offset: int = 0,
    limit: int = 10,
    not_labels: list[str] | None = None,
    labels: list[str] | None = None,
    last_checkin_before: datetime | None = None,
    last_checkin_after: datetime | None = None,
) -> Iterable[models.C2Implant]:
    q = select(models.C2Implant)
    if c2_server_id:
        q = q.where(models.C2Implant.c2_server_id == c2_server_id)
    if last_checkin_before:
        q = q.where(models.C2Implant.last_checkin <= last_checkin_before)
    if last_checkin_after:
        q = q.where(models.C2Implant.last_checkin >= last_checkin_after)
    if not_labels:
        q1 = select(models.LabeledItem.c2_implant_id)
        q1 = q1.where(models.LabeledItem.label_id == models.Label.id)
        for label in not_labels:
            q1 = q1.where(models.Label.name == label)
        q = q.where(models.C2Implant.id.not_in(q1))
    if labels:
        q1 = select(models.LabeledItem.c2_implant_id)
        q1 = q1.where(models.LabeledItem.label_id == models.Label.id)
        for label in labels:
            q1 = q1.where(models.Label.name == label)
        q = q.where(models.C2Implant.id.in_(q1))
    q = q.offset(offset).limit(limit)
    q = q.order_by(models.C2Implant.time_created.desc())
    result = await db.execute(q)
    return result.scalars().unique().all()


@redis_cache(
    key_prefix="c2_implant",
    session_factory=SessionLocal,
    schema=schemas.C2Implant,
    key_param_name="c2_implant_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_c2_implant(
    db: AsyncSession,
    c2_implant_id: str | uuid.UUID,
) -> models.C2Implant | None:
    return await db.get(models.C2Implant, c2_implant_id)


async def get_c2_implant_by_internal_id(
    db: AsyncSession,
    internal_id: str,
    c2_server_id: str,
) -> models.C2Implant | None:
    q = (
        select(models.C2Implant)
        .where(models.C2Implant.internal_id == internal_id)
        .where(models.C2Implant.c2_server_id == c2_server_id)
        .limit(1)
    )
    result = await db.execute(q)
    return result.unique().scalar_one_or_none()


@redis_cache_invalidate(key_prefix="c2_implant", key_param_name="c2_implant_id")
async def update_c2_implant(
    db: AsyncSession,
    c2_implant_id: str | UUID4,
    implant: schemas.C2ImplantUpdate,
) -> models.C2Implant | None:
    q = update(models.C2Implant).where(models.C2Implant.id == c2_implant_id)
    data = implant.model_dump(
        exclude_none=True,
        exclude_defaults=True,
        exclude_unset=True,
    )
    if not data:
        return await db.get(models.C2Implant, c2_implant_id)
    q = q.values(**data)
    await db.execute(q)
    await db.commit()
    return await db.get(models.C2Implant, c2_implant_id)


async def create_or_update_c2_implant(
    db: AsyncSession,
    implant: schemas.C2ImplantCreate,
) -> tuple[bool, models.C2Implant]:
    """Creates the implant in the database, if the implant with that id already exists, updates it.
    returns tuple[bool, C2Implant]
    The bool indicates if the implant was creaed.
    """
    q = select(models.C2Implant).where(
        models.C2Implant.c2_server_id == implant.c2_server_id,
    )
    if implant.internal_id:
        q = q.where(models.C2Implant.internal_id == implant.internal_id)
    res = await db.execute(q)
    db_implant = res.scalars().first()
    if db_implant:
        q = (
            update(models.C2Implant)
            .where(models.C2Implant.id == db_implant.id)
            .values(
                **implant.model_dump(
                    exclude_none=True,
                    exclude_unset=True,
                    exclude_defaults=True,
                ),
            )
        )
        await db.execute(q)
        await db.commit()
        await invalidate_cache_entry("c2_implant", db_implant.id)
        new = False
    else:
        db_implant = models.C2Implant(**implant.model_dump())
        db.add(db_implant)
        await db.commit()
        await db.refresh(db_implant)
        new = True
    return (new, db_implant)


async def recurse_labels_c2_implant(
    db: AsyncSession,
    c2_implant_id: str | UUID4,
) -> Iterable[schemas.Label]:
    q = select(models.Label)
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.c2_implant_id == c2_implant_id)
    resp = await db.execute(q)
    result = [schemas.Label.model_validate(label) for label in resp.scalars().unique().all()]
    q = select(models.Label)
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.host_id == models.C2Implant.host_id)
    q = q.where(models.C2Implant.id == c2_implant_id)
    resp = await db.execute(q)
    result.extend(
        [schemas.Label.model_validate(label) for label in resp.scalars().unique().all()],
    )
    q = select(models.Label)
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.domain_id == models.Host.domain_id)
    q = q.where(models.C2Implant.host_id == models.Host.id)
    q = q.where(models.C2Implant.id == c2_implant_id)
    resp = await db.execute(q)
    result.extend(
        [schemas.Label.model_validate(label) for label in resp.scalars().unique().all()],
    )
    return result
