from typing import Optional

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.database import filters
from harbinger.config.dependencies import current_active_user

router = APIRouter()


@router.get("/", response_model=Page[schemas.Objective], tags=["crud", "objectives"])
async def list_objectives(
    filters: filters.ObjectivesFilter = FilterDepends(filters.ObjectivesFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_objectives_paged(db, filters)


@router.get(
    "/filters", response_model=list[schemas.Filter], tags=["objectives", "crud"]
)
async def objectives_filters(
    filters: filters.ObjectivesFilter = FilterDepends(filters.ObjectivesFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_objectives_filters(db, filters)


@router.get(
    "/{id}", response_model=Optional[schemas.Objective], tags=["crud", "objectives"]
)
async def get_objectives(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_objective(db, id)


@router.post("/", response_model=schemas.ObjectiveCreated, tags=["crud", "objectives"])
async def create_objectives(
    objective: schemas.ObjectiveCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    _, resp = await crud.create_objective(db, objective)
    return resp


@router.put(
    "/{id}", response_model=Optional[schemas.Objective], tags=["crud", "objectives"]
)
async def update_objectives(
    id: UUID4,
    objective: schemas.ObjectiveCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_objective(db, id, objective)
