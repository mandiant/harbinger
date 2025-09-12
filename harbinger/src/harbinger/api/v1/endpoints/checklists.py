from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.Checklist], tags=["crud", "checklists"])
async def list_checklists(
    filters: filters.ChecklistFilter = FilterDepends(filters.ChecklistFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_checklists_paged(db, filters)


@router.get(
    "/filters",
    response_model=list[schemas.Filter],
    tags=["checklists", "crud"],
)
async def checklists_filters(
    filters: filters.ChecklistFilter = FilterDepends(filters.ChecklistFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_checklists_filters(db, filters)


@router.get(
    "/{id}",
    response_model=schemas.Checklist | None,
    tags=["crud", "checklists"],
)
async def get_checklist(
    id: UUID4,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.get_checklist(db, id)


@router.post("/", response_model=schemas.ChecklistCreated, tags=["crud", "checklists"])
async def create_checklist(
    checklists: schemas.ChecklistCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    _, resp = await crud.create_checklist(db, checklists)
    return resp


@router.put(
    "/{id}",
    response_model=schemas.Checklist | None,
    tags=["crud", "checklists"],
)
async def update_checklist(
    id: UUID4,
    checklists: schemas.ChecklistCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.update_checklist(db, id, checklists)
