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


@router.get(
    "/",
    response_model=Page[schemas.CertificateAuthority],
    tags=["crud", "certificate_authorities"],
)
async def list_certificate_authorities(
    filters: filters.CertificateAuthorityFilter = FilterDepends(
        filters.CertificateAuthorityFilter
    ),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_certificate_authorities_paged(db, filters)


@router.get(
    "/filters",
    response_model=list[schemas.Filter],
    tags=["certificate_authorities", "crud"],
)
async def certificate_authorities_filters(
    filters: filters.CertificateAuthorityFilter = FilterDepends(
        filters.CertificateAuthorityFilter
    ),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_certificate_authorities_filters(db, filters)


@router.get(
    "/{id}",
    response_model=Optional[schemas.CertificateAuthority],
    tags=["crud", "certificate_authorities"],
)
async def get_certificate_authoritie(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_certificate_authority(db, id)
