from typing import Annotated

from fastapi import APIRouter, Depends
from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.ManualTimelineTaskCreated,
    tags=["crud", "manual_timeline_tasks"],
)
async def create_manual_timeline_task(
    manual_timeline_tasks: schemas.ManualTimelineTaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.create_manual_timeline_task(db, manual_timeline_tasks)


@router.put(
    "/{id}",
    response_model=schemas.ManualTimelineTask | None,
    tags=["crud", "manual_timeline_tasks"],
)
async def update_manual_timeline_task(
    id: UUID4,
    manual_timeline_tasks: schemas.ManualTimelineTaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.update_manual_timeline_task(db, id, manual_timeline_tasks)
