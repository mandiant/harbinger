from typing import Optional

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger import filters
from harbinger.config.dependencies import current_active_user

router = APIRouter()


@router.get("/", response_model=Page[schemas.Highlight], tags=["crud", "highlights"])
async def list_highlights(
    filters: filters.HighlightFilter = FilterDepends(filters.HighlightFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_highlights_paged(db, filters)


@router.get(
    "/filters", response_model=list[schemas.Filter], tags=["highlights", "crud"]
)
async def highlights_filters(
    filters: filters.HighlightFilter = FilterDepends(filters.HighlightFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_highlights_filters(db, filters)


@router.get(
    "/{id}", response_model=Optional[schemas.Highlight], tags=["crud", "highlights"]
)
async def get_highlight(id: UUID4, user: models.User = Depends(current_active_user)):
    return await crud.get_highlight(id)
