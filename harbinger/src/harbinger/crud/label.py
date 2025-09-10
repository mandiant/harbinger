from typing import Iterable, List, Optional

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from pydantic import UUID4
from sqlalchemy import and_, delete, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import send_label_events


async def get_labels_paged(db: AsyncSession) -> Page[models.Label]:
    return await paginate(
        db, select(models.Label).order_by(models.Label.time_created.desc())
    )


async def get_labels_grouped(db: AsyncSession) -> list[schemas.LabelView]:
    result_dict: dict[str, schemas.LabelView] = {}
    q = select(models.Label).order_by(models.Label.category)
    result = await db.execute(q)
    for entry in result.scalars().all():
        if entry.category not in result_dict:
            result_dict[entry.category] = schemas.LabelView(
                category=entry.category, labels=[]
            )
        result_dict[entry.category].labels.append(entry)
    return list(result_dict.values())


async def get_labeled_items_list(
    db: AsyncSession,
    host_id: str | None = None,
    c2_implant_id: str | None = None,
    retrieve_parents: bool = False,
) -> List[str]:
    q = select(models.Label.name)
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    filters = []
    if host_id:
        filters.append(models.LabeledItem.host_id == host_id)
        if retrieve_parents:
            filters.append(
                and_(
                    models.Host.id == host_id,
                    models.LabeledItem.domain_id == models.Host.domain_id,
                )
            )
    if c2_implant_id:
        filters.append(models.LabeledItem.c2_implant_id == c2_implant_id)
        if retrieve_parents:
            filters.append(
                and_(
                    models.C2Implant.id == c2_implant_id,
                    models.LabeledItem.host_id == models.C2Implant.host_id,
                )
            )
            filters.append(
                and_(
                    models.C2Implant.id == c2_implant_id,
                    models.C2Implant.host_id == models.Host.id,
                    models.LabeledItem.domain_id == models.Host.domain_id,
                )
            )
    if filters:
        q = q.where(or_(*filters))
    else:
        return []
    result = await db.execute(q)
    return [str(name) for name in result.unique().scalars().all()]


async def create_label(db: AsyncSession, label: schemas.LabelCreate) -> models.Label:
    db_label = models.Label(**label.model_dump())
    db.add(db_label)
    await db.commit()
    await db.refresh(db_label)
    return db_label


async def get_label_by_name(db: AsyncSession, name: str) -> Optional[models.Label]:
    q = select(models.Label)
    q = q.where(models.Label.name == name)
    result = await db.execute(q)
    return result.unique().scalar_one_or_none()


async def create_label_item(
    db: AsyncSession, label: schemas.LabeledItemCreate
) -> models.LabeledItem:
    db_label = models.LabeledItem(**label.model_dump())
    db.add(db_label)
    await db.commit()
    await db.refresh(db_label)
    await send_label_events(label)
    return db_label


async def delete_label_item(db: AsyncSession, label: schemas.LabeledItemDelete) -> str:
    q = delete(models.LabeledItem)
    for x, y in label.model_dump().items():
        if y:
            q = q.where(getattr(models.LabeledItem, x) == y)
    await db.execute(q)
    await db.commit()
    await send_label_events(label)
    return "Success"


async def get_label_categories(db: AsyncSession) -> Iterable[str]:
    q = select(models.Label.category).group_by(models.Label.category)
    result = await db.execute(q)
    return result.scalars().all()


async def recurse_labels(db: AsyncSession, timeline_id: str | UUID4) -> Iterable[str]:
    q = select(func.distinct(models.Label.name))
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(
        or_(
            models.LabeledItem.c2_task_id == timeline_id,
            models.LabeledItem.proxy_job_id == timeline_id,
        )
    )
    resp = await db.execute(q)
    result = list(resp.scalars().unique().all())
    q = select(func.distinct(models.Label.name))
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.c2_implant_id == models.C2Task.c2_implant_id)
    q = q.where(models.C2Task.id == timeline_id)
    resp = await db.execute(q)
    result.extend(list(resp.scalars().unique().all()))
    q = select(func.distinct(models.Label.name))
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.host_id == models.C2Implant.host_id)
    q = q.where(models.C2Implant.id == models.C2Task.c2_implant_id)
    q = q.where(models.C2Task.id == timeline_id)
    resp = await db.execute(q)
    result.extend(list(resp.scalars().unique().all()))
    q = select(func.distinct(models.Label.name))
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.domain_id == models.Host.domain_id)
    q = q.where(models.C2Implant.host_id == models.Host.id)
    q = q.where(models.C2Implant.id == models.C2Task.c2_implant_id)
    q = q.where(models.C2Task.id == timeline_id)
    resp = await db.execute(q)
    result.extend(list(resp.scalars().unique().all()))
    return result


async def get_label_names(
    db: AsyncSession, label_ids: list[str]
) -> dict[str, models.Label]:
    q = select(models.Label).where(models.Label.id.in_(label_ids))
    labels = {}
    result = await db.execute(q)
    for entry in result.scalars().unique().all():
        labels[str(entry.id)] = entry
    return labels


async def get_labels_for_q(db: AsyncSession, q) -> list[schemas.Filter]:
    lq = q.group_by(models.LabeledItem.label_id)
    lq = lq.add_columns(models.LabeledItem.label_id)
    lq = lq.order_by(desc("count_1"))
    labels = await db.execute(lq)
    labels_list = list(labels.unique().all())
    label_options: list[schemas.FilterOption] = []
    label_names = await get_label_names(
        db, [str(entry[1]) for entry in labels_list if entry[1]]
    )
    for entry in labels_list:
        if entry[1]:
            label = label_names.get(str(entry[1]))
            if label:
                label_options.append(
                    schemas.FilterOption(
                        name=label.name, count=entry[0], color=label.color
                    )
                )
    lb_entry = schemas.Filter(
        name="labels",
        icon="",
        type="options",
        options=label_options,
        query_name="label__name__in",
        multiple=True,
    )
    return [lb_entry]
