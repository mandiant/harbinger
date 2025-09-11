import ntpath
import uuid
from typing import Iterable, Optional, Tuple

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger import filters
from harbinger.database.cache import (invalidate_cache_entry, redis_cache,
                                      redis_cache_invalidate)
from harbinger.database.database import SessionLocal
from pydantic import UUID4
from sqlalchemy import Select, delete, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import DEFAULT_CACHE_TTL, create_filter_for_column
from .domain import get_or_create_domain
from .host import get_or_create_host
from .label import create_label_item, get_labels_for_q
from .share import get_or_create_share


async def delete_input_files(
    db: AsyncSession,
    proxy_job_id: str | UUID4 | None = None,
    c2_job_id: str | UUID4 | None = None,
) -> None:
    q = delete(models.InputFile)
    if proxy_job_id:
        q = q.where(models.InputFile.proxy_job_id == proxy_job_id)
    elif c2_job_id:
        q = q.where(models.InputFile.c2_job_id == c2_job_id)
    else:
        return
    await db.execute(q)
    await db.commit()


async def create_input_file(
    db: AsyncSession,
    file_id: str,
    proxy_job_id: str | UUID4 | None = None,
    c2_job_id: str | UUID4 | None = None,
) -> models.InputFile:
    input_db = models.InputFile(
        file_id=file_id, c2_job_id=c2_job_id, proxy_job_id=proxy_job_id
    )
    db.add(input_db)
    await db.commit()
    await db.refresh(input_db)
    return input_db


async def add_file(
    db: AsyncSession,
    filename: str,
    bucket: str,
    path: str,
    filetype: str = "",
    job_id: str | None = None,
    id: str | uuid.UUID | None = None,
    c2_implant_id: str | uuid.UUID | None = None,
    c2_task_id: str | uuid.UUID | None = None,
    manual_timeline_task_id: str | uuid.UUID | None = None,
) -> models.File:
    file = models.File(
        id=id,
        job_id=job_id,
        filename=filename,
        bucket=bucket,
        path=path,
        filetype=filetype,
        c2_implant_id=c2_implant_id,
        c2_task_id=c2_task_id,
        manual_timeline_task_id=manual_timeline_task_id,
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file


@redis_cache_invalidate(key_prefix="file", key_param_name="file_id")
async def update_file(
    db: AsyncSession, file_id: str | uuid.UUID, file: schemas.FileUpdate
) -> None:
    q = update(models.File).where(models.File.id == file_id).values(**file.model_dump())
    await db.execute(q)
    await db.commit()


@redis_cache_invalidate(key_prefix="file", key_param_name="file_id")
async def update_file_path(
    db: AsyncSession, file_id: str | uuid.UUID, path: str
) -> None:
    q = update(models.File).where(models.File.id == file_id).values(path=path)
    await db.execute(q)
    await db.commit()


@redis_cache(
    key_prefix="file",
    session_factory=SessionLocal,
    schema=schemas.File,
    key_param_name="file_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_file(db: AsyncSession, file_id: str | uuid.UUID) -> Optional[models.File]:
    return await db.get(models.File, file_id)


async def get_files(
    db: AsyncSession, filters: filters.FileFilter
) -> Iterable[models.File]:
    """Gets files based on a filter."""
    q: Select = select(models.File)
    q = q.outerjoin(models.File.labels)
    q = filters.filter(q)
    try:
        q = filters.sort(q)
    except NotImplementedError:
        pass
    q = q.group_by(models.File.id)
    result = await db.execute(q)
    return result.unique().scalars().all()


async def get_files_paged(
    db: AsyncSession, file_filters: filters.FileFilter
) -> Page[models.File]:
    q: Select = select(models.File)
    q = q.outerjoin(models.File.labels)
    q = file_filters.filter(q)
    try:
        q = file_filters.sort(q)
    except NotImplementedError:
        pass
    q = q.group_by(models.File.id)
    return await paginate(db, q)


async def get_file_filters(
    db: AsyncSession, file_filters: filters.FileFilter
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.File.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = file_filters.filter(q)
    ft_entry = await create_filter_for_column(
        db, q, models.File.filetype, "filetype", "filetype"
    )
    result.append(ft_entry)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


async def search_files(
    db: AsyncSession, file_filters: filters.FileFilter, offset: int = 0, limit: int = 10
) -> Iterable[models.File]:
    q = select(models.File).outerjoin(models.LabeledItem).outerjoin(models.Label)
    q = file_filters.filter(q)
    result = await db.execute(q.offset(offset).limit(limit))
    return result.scalars().unique().all()


@redis_cache_invalidate(key_prefix="file", key_param_name="file_id")
async def update_file_type(
    db: AsyncSession, file_id: str | uuid.UUID, filetype: schemas.FileType | str | None
) -> Optional[models.File]:
    q = update(models.File).where(models.File.id == file_id).values(filetype=filetype)
    await db.execute(q)
    await db.commit()


async def create_share_file(
    db: AsyncSession, share_file: schemas.ShareFileCreate
) -> models.ShareFile:
    q = insert(models.ShareFile).values(**share_file.model_dump())
    data = share_file.model_dump()
    indexed = data.pop("indexed")
    if indexed:
        data["indexed"] = True
    update_stmt = q.on_conflict_do_update("share_files_unc_path", set_=data)
    result = await db.scalars(
        update_stmt.returning(models.ShareFile),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    return result.unique().one()


async def set_share_file_downloaded(
    db: AsyncSession, share_file_id: str | UUID4
) -> None:
    await db.execute(
        update(models.ShareFile)
        .where(models.ShareFile.id == share_file_id)
        .values(downloaded=True)
    )
    await db.commit()
    await invalidate_cache_entry("share_file", share_file_id)


async def list_share_files_paged(
    db: AsyncSession,
    share_id: str | UUID4 | None = None,
    depth: int = -1,
    parent_id: str | UUID4 | None = None,
    search: str = "",
    labels_only: bool = False,
) -> Page[models.ShareFile]:
    q = select(models.ShareFile)
    if share_id:
        q = q.where(models.ShareFile.share_id == share_id)
    if depth > -1:
        q = q.where(models.ShareFile.depth == depth)
    if parent_id:
        q = q.where(models.ShareFile.parent_id == parent_id)
    if search:
        q = q.where(models.ShareFile.unc_path.ilike(f"%{search}%"))
    if labels_only:
        q = q.where(models.LabeledItem.share_file_id == models.ShareFile.id)
    q = q.order_by(models.ShareFile.name.asc())
    return await paginate(db, q)


async def list_share_files(
    db: AsyncSession,
    share_id: str | UUID4 | None = None,
    depth: int = -1,
    parent_id: str | UUID4 | None = None,
    search: str = "",
    labels_only: bool = False,
    type: str = "",
    indexed: bool | None = None,
    downloaded: bool | None = None,
    max_size: int = 0,
    limit: int = 0,
) -> Iterable[models.ShareFile]:
    q = select(models.ShareFile)
    if share_id:
        q = q.where(models.ShareFile.share_id == share_id)
    if depth > -1:
        q = q.where(models.ShareFile.depth == depth)
    if parent_id:
        q = q.where(models.ShareFile.parent_id == parent_id)
    if search:
        q = q.where(models.ShareFile.unc_path.ilike(f"%{search}%"))
    if labels_only:
        q = q.where(models.LabeledItem.share_file_id == models.ShareFile.id)
    if indexed is not None:
        q = q.where(models.ShareFile.indexed == indexed)
    if type:
        q = q.where(models.ShareFile.type == type)
    if downloaded is not None:
        q = q.where(models.ShareFile.downloaded == downloaded)
    if max_size:
        q = q.where(models.ShareFile.size < max_size)
    q = q.order_by(models.ShareFile.name.asc())
    if limit:
        q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_share_files_paged(
    db: AsyncSession, filters: filters.ShareFileFilter
) -> Page[models.ShareFile]:
    q: Select = select(models.ShareFile)
    q = q.outerjoin(models.ShareFile.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.ShareFile.id)
    return await paginate(db, q)


async def get_share_files(
    db: AsyncSession, filters: filters.ShareFileFilter, offset: int = 0, limit: int = 10
) -> Iterable[models.ShareFile]:
    q: Select = select(models.ShareFile)
    q = q.outerjoin(models.ShareFile.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_share_file_filters(db: AsyncSession, filters: filters.ShareFileFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.ShareFile.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["type", "downloaded", "indexed", "depth", "extension"]:
        res = await create_filter_for_column(
            db, q, getattr(models.ShareFile, field), field, field
        )
        result.append(res)
    return result


@redis_cache(
    key_prefix="share_file",
    session_factory=SessionLocal,
    schema=schemas.ShareFile,
    key_param_name="id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_share_file(
    db: AsyncSession, id: UUID4 | str
) -> Optional[models.ShareFile]:
    return await db.get(models.ShareFile, id)


@redis_cache_invalidate(key_prefix="share_file", key_param_name="id")
async def update_share_file(
    db: AsyncSession, id: str | uuid.UUID, share_file: schemas.ShareFileUpdate
) -> None:
    to_update = share_file.model_dump(
        exclude_unset=True, exclude_defaults=True, exclude_none=True
    )
    if to_update:
        q = (
            update(models.ShareFile)
            .where(models.ShareFile.id == id)
            .values(**to_update)
        )
        await db.execute(q)
        await db.commit()


async def save_parsed_share_file(
    db: AsyncSession, file: schemas.BaseParsedShareFile
) -> Tuple[models.Share, models.ShareFile]:
    domain_id = None
    host_id = None
    if file.domain:
        d = await get_or_create_domain(db, file.domain)
        domain_id = d.id
    _, h = await get_or_create_host(db, file.hostname, domain_id)
    host_id = h.id
    _, share_db = await get_or_create_share(
        db,
        schemas.ShareCreate(
            host_id=host_id, name=file.sharename, unc_path=file.share_unc_path
        ),
    )
    parent_id = None
    for parent in file.parents:
        parent_share_file = schemas.ShareFileCreate(
            type=parent.type,
            parent_id=parent_id,
            size=parent.size,
            share_id=share_db.id,
            indexed=parent.indexed,
            depth=parent.depth,
            name=parent.name,
            unc_path=parent.unc_path,
        )
        parent_db = await create_share_file(db, parent_share_file)
        parent_id = parent_db.id
    share_file = schemas.ShareFileCreate(
        type=file.type,
        parent_id=parent_id,
        share_id=share_db.id,
        size=file.size,
        last_modified=file.timestamp,
        unc_path=file.unc_path,
        name=file.name,
        depth=file.depth,
        indexed=True,
    )
    parent_id = None
    if file.depth == 0:
        await create_label_item(
            db,
            schemas.LabeledItemCreate(
                label_id="851853d0-e540-4185-b46e-cf2e0cc63aa8", share_id=share_db.id
            ),
        )
    else:
        share_file = await create_share_file(db, share_file)
        parent_id = share_file.id
        await db.commit()
    if file.children:
        await save_objects(
            db,
            entries=file.children,
            parent_name=file.unc_path,
            share_id=share_db.id,
            depth=file.depth,
            parent_id=parent_id,
        )
    await db.commit()
    return (share_db, share_file)


async def get_file_by_hash(db: AsyncSession, hash_value: str) -> Optional[models.File]:
    hash_value = hash_value.lower()
    q = await db.execute(
        select(models.File).where(
            or_(
                models.File.md5sum == hash_value,
                models.File.sha1sum == hash_value,
                models.File.sha256sum == hash_value,
            )
        )
    )
    return q.scalars().first()

async def save_objects(
    db: AsyncSession,
    entries: list[schemas.BaseParsedShareFile],
    parent_name: str,
    share_id: str | uuid.UUID,
    depth: int,
    parent_id: str | uuid.UUID | None,
) -> None:
    for entry in entries:
        unc_file_path = ntpath.join(parent_name, entry.name)
        file = schemas.ShareFileCreate(
            type=entry.type,
            share_id=share_id,
            size=entry.size,
            last_modified=entry.timestamp,
            unc_path=unc_file_path,
            name=entry.name,
            depth=depth + 1,
            parent_id=parent_id,
            indexed=len(entry.children) > 0 and entry.type == "dir",
        )
        file_db = await create_share_file(db, file)
        await db.commit()
        await save_objects(
            db, entry.children, unc_file_path, share_id, depth + 1, file_db.id
        )
