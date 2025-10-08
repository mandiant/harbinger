import re
import uuid
from collections.abc import Iterable
from typing import Any

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import models, schemas


async def _process_dynamic_argument_ids(db: AsyncSession, arguments: dict[str, Any]):
    """Helper function to dynamically process arguments ending with '_id<number>'
    and replace them with the corresponding model instance, preserving the number.
    """
    model_mappings = {
        "credential": models.Credential,
        "c2_implant": models.C2Implant,
        "kerberos": models.Kerberos,
        "file": models.File,
    }
    arguments_to_process = list(arguments.keys())
    for arg_key in arguments_to_process:
        for base_prefix, model_class in model_mappings.items():
            match = re.fullmatch(f"{base_prefix}_id(\\d*)", arg_key)
            if match:
                suffix = match.group(1)
                item_id = arguments[arg_key]
                item = await db.get(model_class, item_id)
                if item:
                    new_key = f"{base_prefix}{suffix}"
                    arguments[new_key] = item
                break


async def get_highest_process_number(db: AsyncSession, host_id: str | uuid.UUID) -> int:
    q = select(func.max(models.Process.number)).where(models.Process.host_id == host_id)
    result = await db.execute(q)
    return result.scalar_one_or_none() or 0


async def create_process(
    db: AsyncSession,
    process: schemas.ProcessCreate,
) -> models.Process:
    process_db = models.Process(**process.model_dump())
    db.add(process_db)
    await db.commit()
    await db.refresh(process_db)
    return process_db


async def get_process_numbers(
    db: AsyncSession,
    host_id: str = "",
    c2_implant_id: str = "",
) -> Iterable[int]:
    q = select(models.Process.number)
    if host_id:
        q = q.where(models.Process.host_id == host_id)
    if c2_implant_id:
        q = q.where(models.Process.c2_implant_id == c2_implant_id)
    result = await db.execute(q.order_by(models.Process.number))
    return result.scalars().unique().all()


async def get_processes_paged(
    db: AsyncSession,
    host_id: str = "",
    c2_implant_id: str = "",
    number: int = 0,
    parent_process_id: str = "",
    only_top_processes: bool = False,
    labels_only: bool = False,
    search: str = "",
) -> Page[models.Process]:
    q = select(models.Process)
    if host_id:
        q = q.where(models.Process.host_id == host_id)
    if c2_implant_id:
        q = q.where(models.Process.c2_implant_id == c2_implant_id)
    if number:
        q = q.where(models.Process.number == number)
    if only_top_processes:
        q = q.where(models.Process.parent_process_id == 0)
    if parent_process_id:
        q = q.where(models.Process.parent_process_id == parent_process_id)
    if search:
        q = q.where(models.Process.name.ilike(f"%{search}%"))
    if labels_only:
        q = q.where(models.LabeledItem.process_id == models.Process.id)
    return await apaginate(db, q.order_by(models.Process.process_id.asc()))


async def get_processes(
    db: AsyncSession,
    host_id: str = "",
    c2_implant_id: str = "",
    number: int = 0,
    parent_process_id: str = "",
    offset: int = 0,
    limit: int = 10,
    with_users_only: bool = False,
    only_top_processes: bool = False,
) -> Iterable[models.Process]:
    q = select(models.Process)
    if host_id:
        q = q.where(models.Process.host_id == host_id)
    if c2_implant_id:
        q = q.where(models.Process.c2_implant_id == c2_implant_id)
    if number:
        q = q.where(models.Process.number == number)
    if only_top_processes:
        q = q.where(models.Process.parent_process_id == 0)
    if parent_process_id:
        q = q.where(models.Process.parent_process_id == parent_process_id)
    if with_users_only:
        q = q.where(~(models.Process.user == ""))
    q = q.limit(limit).offset(offset)
    result = await db.execute(q.order_by(models.Process.process_id.asc()))
    return result.scalars().unique().all()
