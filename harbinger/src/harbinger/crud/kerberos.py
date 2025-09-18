from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy import exc, select
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import models, schemas


async def get_or_create_kerberos(
    db: AsyncSession,
    kerberos: schemas.KerberosCreate,
) -> tuple[bool, models.Kerberos]:
    q = (
        select(models.Kerberos)
        .where(models.Kerberos.client == kerberos.client)
        .where(models.Kerberos.server == kerberos.server)
        .where(models.Kerberos.key == kerberos.key)
        .where(models.Kerberos.auth == kerberos.auth)
        .where(models.Kerberos.start == kerberos.start)
        .where(models.Kerberos.end == kerberos.end)
        .where(models.Kerberos.renew == kerberos.renew)
        .where(models.Kerberos.keytype == kerberos.keytype)
    )
    res = await db.execute(q)
    try:
        kerberos = res.scalars().unique().one()
        return (False, kerberos)
    except exc.NoResultFound:
        kerberos = models.Kerberos(**kerberos.model_dump())
        db.add(kerberos)
        await db.commit()
        await db.refresh(kerberos)
        return (True, kerberos)


async def get_kerberos_paged(
    db: AsyncSession,
    search: str = "",
) -> Page[models.Kerberos]:
    q = select(models.Kerberos)
    if search:
        q = q.filter(models.Kerberos.client.ilike(f"%{search}%"))
    return await paginate(db, q.order_by(models.Kerberos.time_created.desc()))


async def get_kerberos(
    db: AsyncSession,
    kerberos_id: str | UUID4,
) -> models.Kerberos | None:
    return await db.get(models.Kerberos, kerberos_id)
