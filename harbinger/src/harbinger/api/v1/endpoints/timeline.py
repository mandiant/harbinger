from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.database import filters

router = APIRouter()


@router.get("/", response_model=Page[schemas.TimeLine], tags=["timeline", "crud"])
async def timeline(
    filters: filters.TimeLineFilter = FilterDepends(filters.TimeLineFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_timeline_paged(db, filters=filters)


@router.get("/filters", response_model=list[schemas.Filter], tags=["timeline", "crud"])
async def timeline_filters(
    filters: filters.TimeLineFilter = FilterDepends(filters.TimeLineFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_timeline_filters(db, filters)
