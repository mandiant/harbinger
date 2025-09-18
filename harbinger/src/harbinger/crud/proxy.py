from collections.abc import Iterable

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy import Select, exc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas

from ._common import create_filter_for_column
from .label import get_labels_for_q


async def get_proxy(db: AsyncSession, proxy_id: str | UUID4) -> models.Proxy | None:
    return await db.get(models.Proxy, proxy_id)


async def get_proxy_filters(db: AsyncSession, filters: filters.ProxyFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Proxy.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["host", "type", "status", "remote_hostname"]:
        res = await create_filter_for_column(
            db,
            q,
            getattr(models.Proxy, field),
            field,
            field,
        )
        result.append(res)
    return result


async def create_proxy(db: AsyncSession, proxy: schemas.ProxyCreate) -> models.Proxy:
    db_proxy = models.Proxy(**proxy.model_dump())
    db.add(db_proxy)
    await db.commit()
    await db.refresh(db_proxy)
    return db_proxy


async def update_or_create_proxy(
    db: AsyncSession,
    proxy: schemas.ProxyCreate,
) -> tuple[bool, models.Proxy]:
    q = (
        select(models.Proxy)
        .where(models.Proxy.type == proxy.type.value)
        .where(models.Proxy.host == proxy.host)
        .where(models.Proxy.port == proxy.port)
    )
    if proxy.c2_server_id:
        q = q.where(models.Proxy.c2_server_id == proxy.c2_server_id)
    if proxy.internal_id:
        q = q.where(models.Proxy.internal_id == proxy.internal_id)
    if proxy.c2_task_id:
        q = q.where(models.Proxy.c2_task_id == proxy.c2_task_id)
    if proxy.c2_implant_id:
        q = q.where(models.Proxy.c2_implant_id == proxy.c2_implant_id)
    new = False
    resp = await db.execute(q)
    try:
        proxy_db = resp.scalars().unique().one()
        new = False
    except exc.NoResultFound:
        proxy_db = models.Proxy(**proxy.model_dump())
        proxy_db.type = proxy.type.value
        new = True
    proxy_db.status = proxy.status.value
    db.add(proxy_db)
    await db.commit()
    await db.refresh(proxy_db)
    return (new, proxy_db)


async def get_proxies_paged(
    db: AsyncSession,
    filters: filters.ProxyFilter,
) -> Page[models.Proxy]:
    q: Select = select(models.Proxy)
    q = q.outerjoin(models.Proxy.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Proxy.id)
    return await paginate(db, q)


async def get_proxies(
    db: AsyncSession,
    filters: filters.ProxyFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Proxy]:
    q: Select = select(models.Proxy)
    q = q.outerjoin(models.Proxy.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()
