from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.Action], tags=["crud", "actions"])
async def get_actions(
    filters: filters.ActionFilter = FilterDepends(filters.ActionFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_actions_paged(db, filters)


@router.get("/filters", response_model=list[schemas.Filter], tags=["actions", "crud"])
async def action_filters(
    filters: filters.ActionFilter = FilterDepends(filters.ActionFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_action_filters(db, filters)


@router.get("/{id}", response_model=schemas.Action | None, tags=["crud", "actions"])
async def get_action(
    id: UUID4,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.get_action(db, id)
