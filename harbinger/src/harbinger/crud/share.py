from typing import Iterable, Optional, Tuple

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger.database import filters
from harbinger.database.cache import redis_cache, redis_cache_fixed_key
from harbinger.database.database import SessionLocal
from pydantic import UUID4
from sqlalchemy import Select, exc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import DEFAULT_CACHE_TTL
from .label import create_label_item, get_labels_for_q


async def get_or_create_share(
    db: AsyncSession, share: schemas.ShareCreate
) -> Tuple[bool, models.Share]:
    s = (
        select(models.Share)
        .where(models.Share.name == share.name)
        .where(models.Share.host_id == share.host_id)
    )
    q = await db.execute(s)
    db_share = q.scalars().first()
    if not db_share:
        db_share = models.Share(**share.model_dump())
        db.add(db_share)
        try:
            await db.commit()
            await db.refresh(db_share)
            if share.name and (
                "$" in share.name
                or share.name.lower()
                in ["sysvol", "wsuscontent", "wsustemp", "updateservicespackages"]
            ):
                await create_label_item(
                    db,
                    label=schemas.LabeledItemCreate(
                        label_id="3f061979-055d-473f-ba15-d7b508f0ba83",
                        share_id=db_share.id,
                    ),
                )
            return (True, db_share)
        except exc.IntegrityError:
            await db.rollback()
            return await get_or_create_share(db, share)
    return (False, db_share)


async def list_shares_paged(
    db, share_filters: filters.ShareFilter
) -> Page[models.Share]:
    q: Select = (
        select(models.Share).outerjoin(models.Share.labels).group_by(models.Share.id)
    )
    q = share_filters.filter(q)
    return await paginate(db, q)


async def get_shares(
    db: AsyncSession, filters: filters.ShareFilter, offset: int = 0, limit: int = 10
) -> Iterable[models.Share]:
    q: Select = select(models.Share)
    q = q.outerjoin(models.Share.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_share_filters(
    db: AsyncSession, share_filters: filters.ShareFilter
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Share.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = share_filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


@redis_cache(
    key_prefix="share",
    session_factory=SessionLocal,
    schema=schemas.Share,
    key_param_name="share_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_share(db: AsyncSession, share_id: str | UUID4) -> Optional[models.Share]:
    return await db.get(models.Share, share_id)


@redis_cache_fixed_key(
    cache_key="share_statistics",
    session_factory=SessionLocal,
    schema=schemas.StatisticsItems,
)
async def get_share_statistics(db: AsyncSession) -> dict:
    stats = {}
    q = select(func.count(models.Share.id))
    result = await db.execute(q)
    entry = result.scalars().first()
    stats["Shares"] = entry
    q = select(func.count(models.ShareFile.id))
    result = await db.execute(q)
    entry = result.scalars().first()
    stats["Files"] = entry
    q = select(func.count(models.Highlight.id))
    result = await db.execute(q)
    entry = result.scalars().first()
    stats["Highlights"] = entry
    return dict(items=[dict(key=key, value=value) for key, value in stats.items()])


async def indexer_list_shares(
    db: AsyncSession, max_shares: int = 0, not_label_ids: list[str] | None = None
) -> Iterable[models.Share]:
    """
    List shares
    """
    q = select(models.Share)
    q = q.filter(~models.Share.id.in_(select(models.ShareFile.share_id).distinct()))
    if max_shares > 0:
        q = q.limit(max_shares)
    if not_label_ids:
        q1 = select(models.LabeledItem.share_id)
        q1 = q1.where(models.LabeledItem.label_id.in_(not_label_ids))
        q = q.where(models.Share.id.not_in(q1))
    dq = await db.execute(q)
    return dq.scalars().unique().all()


async def indexer_list_shares_filtered(
    db: AsyncSession,
    max_shares: int = 0,
    not_label_ids: list[str] | None = None,
    depth: int = -1,
    file_type: str = "",
    indexed: bool | None = None,
    search: str = "",
) -> Iterable[str]:
    q = select(models.Share.id)
    if not_label_ids:
        q1 = select(models.LabeledItem.share_id)
        q1 = q1.where(models.LabeledItem.label_id.in_(not_label_ids))
        q = q.where(models.Share.id.not_in(q1))
    q2 = select(models.ShareFile.share_id).where(models.ShareFile.share_id.in_(q))
    if depth > -1:
        q2 = q2.filter(models.ShareFile.depth == depth)
    if file_type:
        q2 = q2.filter(models.ShareFile.type == file_type)
    if indexed is not None:
        q2 = q2.filter(models.ShareFile.indexed == indexed)
    if max_shares > 0:
        q2 = q2.limit(max_shares)
    if search:
        q2 = q2.filter(models.ShareFile.like(f"%{search}%"))
    dq = await db.execute(q2)
    return dq.scalars().unique().all()
