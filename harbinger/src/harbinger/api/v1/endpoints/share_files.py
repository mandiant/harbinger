from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.ShareFile], tags=["crud", "share_files"])
async def list_share_files(
    filters: filters.ShareFileFilter = FilterDepends(filters.ShareFileFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_share_files_paged(db, filters)


@router.get(
    "/filters",
    response_model=list[schemas.Filter],
    tags=["share_files", "crud"],
)
async def share_files_filters(
    filters: filters.ShareFileFilter = FilterDepends(filters.ShareFileFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_share_file_filters(db, filters)


@router.get(
    "/{id}",
    response_model=schemas.ShareFile | None,
    tags=["crud", "share_files"],
)
async def get_share_file(id: UUID4, user: Annotated[models.User, Depends(current_active_user)]):
    return await crud.get_share_file(id)
