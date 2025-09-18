from collections.abc import Iterable

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy import Select, exc, select
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import filters, models


async def get_or_create_password(
    db: AsyncSession,
    password: str | None = "",
    nt_hash: str | None = "",
    aes256_key: str | None = "",
    aes128_key: str | None = "",
) -> models.Password:
    q = select(models.Password)
    if password:
        q = q.where(models.Password.password == password)
    if nt_hash:
        nt_hash = nt_hash.lower()
        q = q.where(models.Password.nt == nt_hash)
    if aes128_key:
        aes128_key = aes128_key.lower()
        q = q.where(models.Password.aes128_key == aes128_key)
    if aes256_key:
        aes256_key = aes256_key.lower()
        q = q.where(models.Password.aes256_key == aes256_key)
    res = await db.execute(q)
    try:
        password_db = res.scalars().unique().one()
    except exc.NoResultFound:
        password_db = models.Password(
            password=password,
            nt=nt_hash,
            aes256_key=aes256_key,
            aes128_key=aes128_key,
        )
        db.add(password_db)
        await db.commit()
        await db.refresh(password_db)
    return password_db


async def get_password(
    db: AsyncSession,
    password_id: str | UUID4,
) -> models.Password | None:
    return await db.get(models.Password, password_id)


async def get_passwords(
    db: AsyncSession,
    search: str = "",
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Password]:
    q = select(models.Password)
    if search:
        q = q.filter(models.Password.password.ilike(f"%{search}%"))
    result = await db.execute(q.offset(offset).limit(limit))
    return result.scalars().unique().all()


async def get_passwords_paged(
    db: AsyncSession,
    filters: filters.PasswordFilter,
) -> Page[models.Password]:
    q: Select = select(models.Password)
    q = q.outerjoin(models.Password.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Password.id)
    return await paginate(db, q)
