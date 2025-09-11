from typing import Iterable, Optional

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger import filters
from harbinger.database.cache import redis_cache, redis_cache_invalidate
from harbinger.database.database import SessionLocal
from pydantic import UUID4
from sqlalchemy import Select, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import DEFAULT_CACHE_TTL
from .label import get_labels_for_q


@redis_cache(
    key_prefix="domain",
    session_factory=SessionLocal,
    schema=schemas.Domain,
    key_param_name="domain_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_domain(
    db: AsyncSession, domain_id: str | UUID4
) -> Optional[models.Domain]:
    return await db.get(models.Domain, domain_id)


async def get_or_create_domain(db: AsyncSession, name: str) -> models.Domain:
    name = name.upper()
    q = await db.execute(
        select(models.Domain).where(
            or_(
                models.Domain.long_name.ilike(name),
                models.Domain.short_name.ilike(name),
            )
        )
    )
    domain = q.scalars().first()
    if not domain:
        domain = models.Domain()
        q = insert(models.Domain)
        if "." in name:
            q = q.values(long_name=name)
            q = q.on_conflict_do_update(
                "domains_long_name_key", set_=dict(long_name=name)
            )
        else:
            q = q.values(short_name=name)
            q = q.on_conflict_do_update(
                "domains_short_name_key", set_=dict(short_name=name)
            )
        result = await db.scalars(
            q.returning(models.Domain), execution_options={"populate_existing": True}
        )
        await db.commit()
        return result.unique().one()
    return domain


async def get_domains_paged(
    db: AsyncSession, filters: filters.DomainFilter
) -> Page[models.Domain]:
    q: Select = select(models.Domain)
    q = q.outerjoin(models.Domain.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Domain.id)
    return await paginate(db, q)


async def get_domains(
    db: AsyncSession, filters: filters.DomainFilter, offset: int = 0, limit: int = 10
) -> Iterable[models.Domain]:
    q: Select = select(models.Domain)
    q = q.outerjoin(models.Domain.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_domains_filters(db: AsyncSession, filters: filters.DomainFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Domain.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


async def create_domain(
    db: AsyncSession, domain: schemas.DomainCreate
) -> models.Domain:
    db_domain = models.Domain(**domain.model_dump())
    db.add(db_domain)
    await db.commit()
    await db.refresh(db_domain)
    return db_domain


@redis_cache_invalidate(key_prefix="domain", key_param_name="domain_id")
async def update_domain(
    db: AsyncSession, domain_id: str | UUID4, domain: schemas.DomainCreate
) -> Optional[models.Domain]:
    domain_db = await db.get(models.Domain, domain_id)
    if domain_db:
        try:
            q = (
                update(models.Domain)
                .where(models.Domain.id == domain_id)
                .values(long_name=domain.long_name, short_name=domain.short_name)
            )
            await db.execute(q)
            await db.commit()
            await db.refresh(domain_db)
            return domain_db
        except IntegrityError:
            await db.rollback()
            return domain_db
    return None


async def get_domain_name_from_host(db: AsyncSession, host_id: str | UUID4) -> str:
    q = (
        select(models.Domain)
        .where(models.Host.domain_id == models.Domain.id)
        .where(models.Host.id == host_id)
    )
    result = await db.execute(q)
    domain_db = result.scalars().first()
    if domain_db:
        if domain_db.long_name:
            return domain_db.long_name
        elif domain_db.short_name:
            return domain_db.short_name
    return ""


async def set_long_name(
    db: AsyncSession, domain_id: str | UUID4, long_name: str
) -> bool:
    try:
        q = (
            update(models.Domain)
            .where(models.Domain.id == domain_id)
            .values(long_name=long_name)
        )
        await db.execute(q)
        await db.commit()
        return True
    except IntegrityError:
        await db.rollback()
        return False
