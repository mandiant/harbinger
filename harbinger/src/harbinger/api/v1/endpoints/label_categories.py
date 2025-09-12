from typing import Annotated

from fastapi import APIRouter, Depends
from harbinger import crud, models
from harbinger.config.dependencies import current_active_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=list[str], tags=["labels", "crud"])
async def get_label_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.get_label_categories(db=db)
