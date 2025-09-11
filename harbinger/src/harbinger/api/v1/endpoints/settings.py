from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.config.dependencies import current_active_user

router = APIRouter()


@router.get("/", response_model=list[schemas.Settings], tags=["settings", "crud"])
async def get_dynamic_settings(
    db: AsyncSession = Depends(get_db), user: models.User = Depends(current_active_user)
):
    return await crud.get_settings(db)


@router.patch("/{setting_id}", response_model=str, tags=["settings", "crud"])
async def save_settings(
    setting_id: UUID4,
    setting: schemas.SettingModify,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    await crud.update_setting(db, setting_id, setting)
    return "ok"
