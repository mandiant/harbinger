from typing import Annotated

from fastapi import APIRouter, Depends
from harbinger import models, schemas
from harbinger.config.dependencies import current_active_user
from harbinger.database import progress_bar

router = APIRouter()


@router.get(
    "/",
    response_model=list[schemas.ProgressBar],
    tags=["crud", "progress_bar"],
)
async def get_progress_bar(user: Annotated[models.User, Depends(current_active_user)]):
    return await progress_bar.get_progress_bars()


@router.delete(
    "/",
    response_model=schemas.StatusResponse,
    tags=["crud", "progress_bar"],
)
async def clear_progress_bars(user: Annotated[models.User, Depends(current_active_user)]):
    result = await progress_bar.get_progress_bars()
    for e in result:
        await progress_bar.delete_progress_bar(e.id)
    return schemas.StatusResponse(message="Cleared")
