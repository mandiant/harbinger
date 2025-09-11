from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.config.dependencies import current_active_user

router = APIRouter()


@router.post("/", response_model=schemas.LabeledItem, tags=["labels", "crud"])
async def create_label_mapping(
    label: schemas.LabeledItemCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_label_item(db=db, label=label)


@router.delete("/", tags=["labels", "crud"])
async def delete_label_mapping(
    label: schemas.LabeledItemDelete,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.delete_label_item(db=db, label=label)
