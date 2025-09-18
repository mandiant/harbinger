from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.Share], tags=["crud", "shares"])
async def list_shares(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
    share_filters: filters.ShareFilter = FilterDepends(filters.ShareFilter),
):
    return await crud.list_shares_paged(db, share_filters)


@router.get("/filters", response_model=list[schemas.Filter], tags=["crud", "shares"])
async def shares_filters(
    db: Annotated[AsyncSession, Depends(get_db)],
    share_filters: filters.ShareFilter = FilterDepends(filters.ShareFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_share_filters(db, share_filters)


@router.get(
    "/{share_id}",
    response_model=schemas.Share | None,
    tags=["crud", "shares"],
)
async def get_share(
    share_id: UUID4,
    user: Annotated[models.User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_share(db, share_id)
