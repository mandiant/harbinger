from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.Domain], tags=["crud", "domains"])
async def list_domains(
    filters: filters.DomainFilter = FilterDepends(filters.DomainFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_domains_paged(db, filters)


@router.get("/filters", response_model=list[schemas.Filter], tags=["domains", "crud"])
async def domains_filters(
    filters: filters.DomainFilter = FilterDepends(filters.DomainFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_domains_filters(db, filters)


@router.get("/{id}", response_model=schemas.Domain | None, tags=["crud", "domains"])
async def get_domain(id: UUID4, user: Annotated[models.User, Depends(current_active_user)]):
    return await crud.get_domain(id)


@router.post("/", response_model=schemas.Domain, tags=["crud", "domains"])
async def create_domain(
    domains: schemas.DomainCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.create_domain(db, domains)


@router.put("/{id}", response_model=schemas.Domain | None, tags=["crud", "domains"])
async def update_domain(
    id: UUID4,
    domains: schemas.DomainCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.update_domain(db, id, domains)
