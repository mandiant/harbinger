import contextlib
from collections.abc import Iterable

from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas
from harbinger.database.cache import redis_cache
from harbinger.database.database import SessionLocal

from ._common import DEFAULT_CACHE_TTL, create_filter_for_column
from .label import get_labels_for_q


async def update_socks_task_summary(
    db,
    socks_task_id: str | UUID4,
    summary: str,
    status: str,
) -> None:
    q = (
        update(models.ProxyJob)
        .where(models.ProxyJob.id == socks_task_id)
        .values(processing_status=status, ai_summary=summary)
    )
    await db.execute(q)
    await db.commit()


async def get_socks_job_filters(
    db: AsyncSession,
    filters: filters.SocksJobFilter,
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.ProxyJob.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    for entry in ["command", "status"]:
        ft_entry = await create_filter_for_column(
            db,
            q,
            getattr(models.ProxyJob, entry),
            entry,
            entry,
        )
        result.append(ft_entry)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


async def create_socks_server(
    db: AsyncSession,
    socks_server: schemas.SocksServerCreate,
) -> models.SocksServer:
    q = insert(models.SocksServer).values(**socks_server.model_dump())
    q = q.on_conflict_do_update(
        models.SocksServer.__table__.primary_key,
        set_={"status": socks_server.status},
    )
    result = await db.scalars(
        q.returning(models.SocksServer),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    return result.unique().one()


@redis_cache(
    key_prefix="socks_server",
    session_factory=SessionLocal,
    schema=schemas.SocksServer,
    key_param_name="id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_socks_server(db: AsyncSession, id: UUID4) -> models.SocksServer | None:
    return await db.get(models.SocksServer, id)


async def list_socks_servers_paged(
    db: AsyncSession,
    filters: filters.SocksServerFilter,
):
    q: Select = select(models.SocksServer)
    q = q.outerjoin(models.SocksServer.labels)
    q = filters.filter(q)
    with contextlib.suppress(NotImplementedError):
        q = filters.sort(q)
    q = q.group_by(models.SocksServer.id)
    return await paginate(db, q)


async def get_socks_servers(
    db: AsyncSession,
    filters: filters.SocksServerFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.SocksServer]:
    q: Select = select(models.SocksServer)
    q = q.outerjoin(models.SocksServer.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def update_socks_server_status(db: AsyncSession, id: UUID4, status: str) -> None:
    q = update(models.SocksServer).where(models.SocksServer.id == id).values(status=status)
    await db.execute(q)
    await db.commit()


async def get_socks_server_filters(
    db: AsyncSession,
    filters: filters.SocksServerFilter,
):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.SocksServer.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["operating_system", "type", "status"]:
        res = await create_filter_for_column(
            db,
            q,
            getattr(models.SocksServer, field),
            field,
            field,
        )
        result.append(res)
    return result
