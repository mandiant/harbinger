from typing import Any

from pydantic import UUID4
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import models, schemas


async def create_setting(db: AsyncSession, setting: schemas.SettingCreate):
    q = insert(models.Setting).values(**setting.model_dump())
    update_stmt = q.on_conflict_do_nothing("name_category")
    await db.execute(update_stmt)
    await db.scalars(
        update_stmt.returning(models.Setting),
        execution_options={"populate_existing": True},
    )
    await db.commit()


async def get_settings(db: AsyncSession) -> list[schemas.Settings]:
    result: list[schemas.Settings] = []
    q = select(models.SettingCategory).order_by(models.SettingCategory.order)
    res = await db.execute(q)
    for entry in res.scalars().all():
        q2 = select(models.Setting).where(models.Setting.category_id == entry.id).order_by(models.Setting.name)
        res2 = await db.execute(q2)
        result.append(
            schemas.Settings(
                name=entry.name,
                icon=entry.icon,
                description=entry.description,
                order=entry.order,
                settings=list(res2.scalars().all()),
            ),
        )
    return result


async def create_setting_category(
    db: AsyncSession,
    category: schemas.SettingCategoryCreate,
) -> models.SettingCategory:
    data = category.model_dump()
    data.pop("settings")
    q = insert(models.SettingCategory).values(**data)
    update_stmt = q.on_conflict_do_update(
        "setting_category_name_key",
        set_={
            "description": category.description,
            "icon": category.icon,
            "order": category.order,
        },
    )
    result = await db.scalars(
        update_stmt.returning(models.SettingCategory),
        execution_options={"populate_existing": True},
    )
    resp = result.unique().one()
    await db.refresh(resp)
    db.expunge(resp)
    await db.commit()
    return resp


async def update_setting(
    db: AsyncSession,
    setting_id: UUID4,
    setting: schemas.SettingModify,
) -> None:
    q = update(models.Setting).where(models.Setting.id == setting_id).values(value=setting.value)
    await db.execute(q)
    await db.commit()


async def get_setting(
    db: AsyncSession,
    category_name: str,
    setting_name: str,
    default: Any,
) -> Any | None:
    q = (
        select(models.Setting.value)
        .where(models.Setting.category_id == models.SettingCategory.id)
        .where(models.SettingCategory.name == category_name)
        .where(models.Setting.name == setting_name)
    )
    resp = await db.execute(q)
    result = resp.scalar_one_or_none()
    if result:
        return result
    return default
