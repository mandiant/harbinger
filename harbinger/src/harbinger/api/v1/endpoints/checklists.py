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


@router.get("/", response_model=Page[schemas.Checklist], tags=["crud", "checklists"])
async def list_checklists(
    filters: filters.ChecklistFilter = FilterDepends(filters.ChecklistFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_checklists_paged(db, filters)


@router.get(
    "/filters", response_model=list[schemas.Filter], tags=["checklists", "crud"]
)
async def checklists_filters(
    filters: filters.ChecklistFilter = FilterDepends(filters.ChecklistFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_checklists_filters(db, filters)


@router.get(
    "/{id}", response_model=Optional[schemas.Checklist], tags=["crud", "checklists"]
)
async def get_checklist(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_checklist(db, id)


@router.post("/", response_model=schemas.ChecklistCreated, tags=["crud", "checklists"])
async def create_checklist(
    checklists: schemas.ChecklistCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    _, resp = await crud.create_checklist(db, checklists)
    return resp


@router.put(
    "/{id}", response_model=Optional[schemas.Checklist], tags=["crud", "checklists"]
)
async def update_checklist(
    id: UUID4,
    checklists: schemas.ChecklistCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_checklist(db, id, checklists)
