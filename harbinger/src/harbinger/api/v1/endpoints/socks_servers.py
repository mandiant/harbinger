from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.SocksServer], tags=["socks", "crud"])
async def list_socks_servers(
    filters: filters.SocksServerFilter = FilterDepends(filters.SocksServerFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.list_socks_servers_paged(db, filters)


@router.get("/filters", response_model=list[schemas.Filter], tags=["socks", "crud"])
async def socks_server_filters(
    filters: filters.SocksServerFilter = FilterDepends(filters.SocksServerFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_socks_server_filters(db, filters)


@router.get("/{server_id}", response_model=schemas.SocksServer | None, tags=["socks", "crud"])
async def get_socks_server(
    server_id: UUID4,
    user: Annotated[models.User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_socks_server(db, server_id)


@router.post("/", response_model=schemas.SocksServer, tags=["socks", "crud"])
async def create_socks_server(
    server: schemas.SocksServerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.create_socks_server(db, server)
