import uuid
from typing import Iterable, Optional, Tuple

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger.database import filters
from harbinger.database.cache import redis_cache_fixed_key
from harbinger.database.database import SessionLocal
from pydantic import UUID4
from sqlalchemy import Select, delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import create_filter_for_column
from .label import get_labels_for_q


async def get_c2_servers_paged(db: AsyncSession) -> Page[models.C2Server]:
    return await paginate(
        db, select(models.C2Server).order_by(models.C2Server.time_created.desc())
    )


async def get_c2_servers(db: AsyncSession) -> Iterable[models.C2Server]:
    q = select(models.C2Server)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_c2_server(
    db: AsyncSession, c2_server_id: str | UUID4
) -> Optional[models.C2Server]:
    return await db.get(models.C2Server, c2_server_id)


async def get_c2_servers_filters(db: AsyncSession, filters: filters.C2ServerFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.C2Server.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["type", "name", "hostname", "username"]:
        res = await create_filter_for_column(
            db, q, getattr(models.C2Server, field), field, field
        )
        result.append(res)
    return result


async def update_c2_server(
    db: AsyncSession, c2_server_id: str, c2_server: schemas.C2ServerCreate
) -> models.C2Server | None:
    q = (
        update(models.C2Server)
        .where(models.C2Server.id == c2_server_id)
        .values(**c2_server.model_dump())
    )
    await db.execute(q)
    await db.commit()
    return await db.get(models.C2Server, c2_server_id)


async def create_c2_server(
    db: AsyncSession, c2_server: schemas.C2ServerCreate
) -> models.C2Server | None:
    db_c2_server = models.C2Server(**c2_server.model_dump())
    db.add(db_c2_server)
    await db.commit()
    await db.refresh(db_c2_server)
    return db_c2_server


async def update_c2_server_status(
    db: AsyncSession, c2_server_id: str | UUID4, status: schemas.C2ServerStatus
):
    q = (
        select(models.C2ServerStatus)
        .where(models.C2ServerStatus.c2_server_id == c2_server_id)
        .where(models.C2ServerStatus.name == status.name)
    )
    res = await db.execute(q)
    status_db = res.scalars().unique().first()
    if status_db:
        q = (
            update(models.C2ServerStatus)
            .where(models.C2ServerStatus.id == status_db.id)
            .values(**status.model_dump())
        )
        await db.execute(q)
        await db.commit()
    else:
        status_db = models.C2ServerStatus(
            **status.model_dump(), c2_server_id=c2_server_id
        )
        db.add(status_db)
        await db.commit()


async def list_c2_server_status(db: AsyncSession) -> Iterable[models.C2ServerStatus]:
    q = select(models.C2ServerStatus)
    result = await db.execute(q)
    return result.scalars().all()


async def delete_c2_server_status(db: AsyncSession, status_id: UUID4 | str) -> None:
    q = delete(models.C2ServerStatus).where(models.C2ServerStatus.id == status_id)
    await db.execute(q)
    await db.commit()


async def delete_c2_server_status_custom(
    db: AsyncSession, c2_server_id: str | UUID4, status: schemas.C2ServerStatus
) -> None:
    q = (
        delete(models.C2ServerStatus)
        .where(models.C2ServerStatus.c2_server_id == c2_server_id)
        .where(models.C2ServerStatus.name == status.name)
    )
    await db.execute(q)
    await db.commit()


@redis_cache_fixed_key(
    cache_key="c2_server_statistics",
    session_factory=SessionLocal,
    schema=schemas.StatisticsItems,
)
async def get_c2_server_statistics(db: AsyncSession) -> dict:
    stats = {}
    c2_server_stats = {}
    icon_map = {
        "Container: running": "check",
        "Container: exited": "close",
        "Container: stopping": "close",
        "Container: restarting": "hourglass",
        "Container: restarted": "hourglass",
        "Container: deleting": "delete",
        "Socks: linux docker": "check",
        "Socks: windows docker": "check",
    }
    q = select(models.C2Server)
    result = await db.execute(q)
    for entry in result.scalars().unique().all():
        q2 = select(models.C2ServerStatus).where(
            models.C2ServerStatus.c2_server_id == entry.id
        )
        result2 = await db.execute(q2)
        found = False
        for status in result2.scalars().unique().all():
            found = True
            if f"Container: {status.status}" not in stats:
                stats[f"Container: {status.status}"] = 0
            stats[f"Container: {status.status}"] += 1
        if not found:
            if "Container: missing" not in stats:
                stats["Container: missing"] = 0
            stats["Container: missing"] += 1
        if entry.type not in c2_server_stats:
            c2_server_stats[entry.type] = 0
        c2_server_stats[entry.type] += 1
    c2_server_stats.update(stats)
    q = select(models.SocksServer)
    result = await db.execute(q)
    for entry in result.scalars().unique().all():
        name = f"Socks: {entry.operating_system} {entry.type}"
        if name not in c2_server_stats:
            c2_server_stats[name] = 0
        c2_server_stats[name] += 1
    return dict(
        items=[
            dict(key=key, value=value, icon=icon_map.get(key, "question_mark"))
            for key, value in c2_server_stats.items()
        ]
    )


async def get_c2_server_types_paged(
    db: AsyncSession, filters: filters.C2ServerTypeFilter
) -> Page[models.C2ServerType]:
    q: Select = select(models.C2ServerType)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.C2ServerType.id)
    return await paginate(db, q)


async def get_c2_server_types(
    db: AsyncSession, id: UUID4
) -> Optional[models.C2ServerType]:
    return await db.get(models.C2ServerType, id)


async def create_c2_server_type(
    db: AsyncSession, c2_server_types: schemas.C2ServerTypeCreate
) -> Tuple[bool, models.C2ServerType]:
    data = c2_server_types.model_dump()
    q = insert(models.C2ServerType).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update(
        models.C2ServerType.__table__.primary_key, set_=data
    )
    result = await db.scalars(
        update_stmt.returning(models.C2ServerType),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    return (result.time_updated == None, result)


async def update_c2_server_type(
    db: AsyncSession, id: str | uuid.UUID, c2_server_types: schemas.C2ServerTypeCreate
) -> None:
    q = (
        update(models.C2ServerType)
        .where(models.C2ServerType.id == id)
        .values(**c2_server_types.model_dump())
    )
    await db.execute(q)
    await db.commit()


async def get_c2_server_type_by_name(
    db: AsyncSession, name: str
) -> Optional[models.C2ServerType]:
    q: Select = select(models.C2ServerType)
    q = q.where(models.C2ServerType.name == name)
    res = await db.execute(q)
    return res.scalars().first()


async def get_c2_server_arguments_paged(
    db: AsyncSession, c2_server_type: UUID4
) -> Page[models.C2ServerArguments]:
    q: Select = select(models.C2ServerArguments)
    q = q.where(models.C2ServerArguments.c2_server_type_id == c2_server_type)
    return await paginate(db, q)


async def get_c2_server_arguments(
    db: AsyncSession, id: UUID4
) -> Optional[models.C2ServerArguments]:
    return await db.get(models.C2ServerArguments, id)


async def create_c2_server_argument(
    db: AsyncSession, c2_server_argument: schemas.C2ServerArgumentsCreate
) -> Tuple[bool, models.C2ServerArguments]:
    data = c2_server_argument.model_dump()
    q = insert(models.C2ServerArguments).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update(
        models.C2ServerArguments.__table__.primary_key, set_=data
    )
    result = await db.scalars(
        update_stmt.returning(models.C2ServerArguments),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    return (result.time_updated == None, result)


async def delete_c2_server_arguments(
    db: AsyncSession, c2_server_type_id: UUID4
) -> None:
    q = delete(models.C2ServerArguments).where(
        models.C2ServerArguments.c2_server_type_id == c2_server_type_id
    )
    await db.execute(q)
    await db.commit()
