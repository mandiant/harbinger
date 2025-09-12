from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/",
    response_model=Page[schemas.C2Implant],
    tags=["c2", "implants", "crud"],
)
async def read_c2_implants(
    implants_filter: filters.ImplantFilter = FilterDepends(filters.ImplantFilter),
    alive_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_implants_paged(db, implants_filter, alive_only)


@router.get(
    "/filters",
    response_model=list[schemas.Filter],
    tags=["c2", "implants", "crud"],
)
async def c2_implant_filters(
    implants_filter: filters.ImplantFilter = FilterDepends(filters.ImplantFilter),
    alive_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_implant_filters(db, implants_filter, alive_only)


@router.get(
    "/{implant_id}",
    response_model=schemas.C2Implant,
    tags=["c2", "implants", "crud"],
)
async def read_c2_implant(
    implant_id: str,
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.get_c2_implant(c2_implant_id=implant_id)
