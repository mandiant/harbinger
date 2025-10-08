import contextlib
import uuid
from collections.abc import Iterable

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import Select, exc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas

from .domain import get_or_create_domain
from .label import get_labels_for_q


async def get_hosts_paged(
    db: AsyncSession,
    host_filters: filters.HostFilter,
) -> Page[models.Host]:
    q = select(models.Host).outerjoin(models.LabeledItem).outerjoin(models.Label)
    q = host_filters.filter(q)
    with contextlib.suppress(NotImplementedError):
        q = host_filters.sort(q)
    q = q.group_by(models.Host.id)
    return await apaginate(db, q)


async def get_hosts(
    db: AsyncSession,
    filters: filters.HostFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Host]:
    q: Select = select(models.Host)
    q = q.outerjoin(models.Host.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_host_filters(
    db: AsyncSession,
    host_filters: filters.HostFilter,
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q = (
        select(func.count(models.Host.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = host_filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


async def get_host(db: AsyncSession, host_id: str | uuid.UUID) -> models.Host | None:
    return await db.get(models.Host, host_id)


async def get_or_create_host(
    db: AsyncSession,
    name: str,
    domain_id: str | uuid.UUID | None = None,
) -> tuple[bool, models.Host]:
    """Searches the name and fqdn for the name of the host.
    If it is not found, creates a host with the name as either name or fqdn depending on the number of dots in the name.
    returns Tuple[bool, Host] with the first value indicating if the host was created.
    """
    created = False
    query = select(models.Host).where(
        or_(models.Host.name.ilike(name), models.Host.fqdn.ilike(name)),
    )
    if domain_id:
        query = query.where(
            or_(models.Host.domain_id == domain_id, models.Host.domain_id is None),
        )
    q = await db.execute(query)
    host = q.scalars().unique().first()
    if not host:
        created = True
        host = models.Host()
        if domain_id:
            host.domain_id = domain_id
        if name.count(".") == 0:
            host.name = name
        else:
            host.fqdn = name
            if not domain_id:
                name, domain = name.split(".", 1)
                host.name = name
            domain = await get_or_create_domain(db, domain)
            host.domain_id = domain.id
            domain_id = domain.id
        db.add(host)
        try:
            await db.commit()
            await db.refresh(host)
        except exc.IntegrityError:
            await db.rollback()
            created, host = await get_or_create_host(db, name, domain_id)
    return (created, host)


async def update_host(
    db: AsyncSession,
    host_id: str | uuid.UUID,
    host: schemas.HostBase,
) -> models.Host | None:
    q = (
        update(models.Host)
        .where(models.Host.id == host_id)
        .values(
            **host.model_dump(
                exclude_unset=True,
                exclude_defaults=True,
                exclude_none=True,
            ),
        )
    )
    await db.execute(q)
    await db.commit()
    return await db.get(models.Host, host_id)
