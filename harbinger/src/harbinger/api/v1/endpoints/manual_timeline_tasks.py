from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.config.dependencies import current_active_user

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.ManualTimelineTaskCreated,
    tags=["crud", "manual_timeline_tasks"],
)
async def create_manual_timeline_task(
    manual_timeline_tasks: schemas.ManualTimelineTaskCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_manual_timeline_task(db, manual_timeline_tasks)


@router.put(
    "/{id}",
    response_model=Optional[schemas.ManualTimelineTask],
    tags=["crud", "manual_timeline_tasks"],
)
async def update_manual_timeline_task(
    id: UUID4,
    manual_timeline_tasks: schemas.ManualTimelineTaskCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_manual_timeline_task(db, id, manual_timeline_tasks)
