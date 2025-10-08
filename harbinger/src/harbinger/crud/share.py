from collections.abc import Iterable

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from pydantic import UUID4
from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas

from .label import create_label_item, get_labels_for_q


async def get_or_create_share(
    db: AsyncSession,
    share: schemas.ShareCreate,
) -> models.Share:
    """
    Atomically gets or creates a Share record using an INSERT ... ON CONFLICT statement.
    """
    insert_stmt = insert(models.Share).values(**share.model_dump())

    # This statement tries to insert. If a share with the same (name, host_id)
    # already exists, it does nothing and returns the existing one.
    do_nothing_stmt = insert_stmt.on_conflict_do_nothing(index_elements=["name", "host_id"])
    await db.execute(do_nothing_stmt)

    # Now, fetch the share, which is guaranteed to exist.
    select_stmt = select(models.Share).where(models.Share.name == share.name, models.Share.host_id == share.host_id)
    db_share = (await db.execute(select_stmt)).unique().scalar_one()

    # Eagerly load any relationships you might need later.
    await db.refresh(db_share, ["labels"])

    # Perform additional logic like adding a label
    is_admin_share = share.name and (
        "$" in share.name or share.name.lower() in ["sysvol", "wsuscontent", "wsustemp", "updateservicespackages"]
    )
    if is_admin_share:
        await create_label_item(
            db,
            label=schemas.LabeledItemCreate(
                label_id="3f061979-055d-473f-ba15-d7b508f0ba83",
                object_id=db_share.id,  # Assuming object_id is the correct field
            ),
        )
    await db.refresh(db_share, ["labels"])
    db.expunge(db_share)
    await db.commit()
    return db_share


# async def get_or_create_share(
#     db: AsyncSession,
#     share: schemas.ShareCreate,
# ) -> tuple[bool, models.Share]:
#     s = select(models.Share).where(models.Share.name == share.name).where(models.Share.host_id == share.host_id)
#     q = await db.execute(s)
#     db_share = q.scalars().first()
#     if not db_share:
#         db_share = models.Share(**share.model_dump())
#         db.add(db_share)
#         try:
#             await db.refresh(db_share)
#             db.expunge(db_share)
#             await db.commit()
#             if share.name and (
#                 "$" in share.name
#                 or share.name.lower() in ["sysvol", "wsuscontent", "wsustemp", "updateservicespackages"]
#             ):
#                 await create_label_item(
#                     db,
#                     label=schemas.LabeledItemCreate(
#                         label_id="3f061979-055d-473f-ba15-d7b508f0ba83",
#                         share_id=db_share.id,
#                     ),
#                 )
#             return (True, db_share)
#         except exc.IntegrityError:
#             await db.rollback()
#             return await get_or_create_share(db, share)
#     return (False, db_share)


async def list_shares_paged(
    db,
    share_filters: filters.ShareFilter,
) -> Page[models.Share]:
    q: Select = select(models.Share).outerjoin(models.Share.labels).group_by(models.Share.id)
    q = share_filters.filter(q)
    return await apaginate(db, q)


async def get_shares(
    db: AsyncSession,
    filters: filters.ShareFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Share]:
    q: Select = select(models.Share)
    q = q.outerjoin(models.Share.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_share_filters(
    db: AsyncSession,
    share_filters: filters.ShareFilter,
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


async def get_share(db: AsyncSession, share_id: str | UUID4) -> models.Share | None:
    return await db.get(models.Share, share_id)


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
    return {"items": [{"key": key, "value": value} for key, value in stats.items()]}


async def indexer_list_shares(
    db: AsyncSession,
    max_shares: int = 0,
    not_label_ids: list[str] | None = None,
) -> Iterable[models.Share]:
    """List shares"""
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
