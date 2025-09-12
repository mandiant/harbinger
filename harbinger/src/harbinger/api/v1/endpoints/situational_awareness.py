from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/",
    response_model=Page[schemas.SituationalAwareness],
    tags=["situational_awareness", "crud"],
)
async def list_situational_awareness(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
    filters: filters.SituationalAwarenessFilter = FilterDepends(
        filters.SituationalAwarenessFilter,
    ),
):
    return await crud.list_situational_awarenesss_paged(db, filters=filters)


@router.get(
    "/filters",
    response_model=list[schemas.Filter],
    tags=["situational_awarenesss", "crud"],
)
async def situational_awarenesss_filters(
    filters: filters.SituationalAwarenessFilter = FilterDepends(
        filters.SituationalAwarenessFilter,
    ),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_situational_awarenesss_filters(db, filters)


@router.post(
    "/",
    response_model=schemas.SituationalAwareness,
    tags=["situational_awareness", "crud"],
)
async def create_situational_awareness(
    sa: schemas.SituationalAwarenessCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    created, sa_db = await crud.get_or_create_situational_awareness(db, sa=sa)
    return sa_db


@router.put(
    "/{sa_id}",
    response_model=schemas.SituationalAwareness | None,
    tags=["situational_awareness", "crud"],
)
async def update_situational_awareness(
    sa_id: UUID4,
    sa: schemas.SituationalAwarenessCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    await crud.update_situational_awareness(db, sa_id=sa_id, sa=sa)
    return crud.get_situational_awareness(sa_id=sa_id)


@router.delete("/{sa_id}", tags=["situational_awareness", "crud"])
async def delete_situational_awareness(
    sa_id: UUID4,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    await crud.delete_situational_awareness(db, sa_id=sa_id)
    return "Success"
