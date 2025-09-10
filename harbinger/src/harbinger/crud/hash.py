from typing import Iterable, Optional, Tuple

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger.database.cache import redis_cache
from harbinger.database.database import SessionLocal
from pydantic import UUID4
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ._common import DEFAULT_CACHE_TTL


async def create_hash(
    db: AsyncSession, hash: schemas.HashCreate
) -> Tuple[bool, models.Hash]:
    q = select(models.Hash).where(models.Hash.hash == hash.hash)
    result = await db.execute(q)
    hash_db = result.scalars().first()
    if hash_db:
        return (False, hash_db)
    else:
        hash_db = models.Hash(**hash.model_dump())
        db.add(hash_db)
        await db.commit()
        await db.refresh(hash_db)
        return (True, hash_db)


@redis_cache(
    key_prefix="hash",
    session_factory=SessionLocal,
    schema=schemas.Hash,
    key_param_name="hash_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_hash(db: AsyncSession, hash_id: UUID4 | str) -> Optional[models.Hash]:
    return await db.get(models.Hash, hash_id)


async def list_hashes_paged(db: AsyncSession) -> Page[models.Hash]:
    q = select(models.Hash)
    return await paginate(db, q)


async def list_hashes(db: AsyncSession) -> Iterable[models.Hash]:
    q = select(models.Hash).order_by(models.Hash.time_created.desc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def delete_hash(db: AsyncSession, hash_id: UUID4 | str) -> None:
    q = delete(models.Hash).where(models.Hash.id == hash_id)
    await db.execute(q)
