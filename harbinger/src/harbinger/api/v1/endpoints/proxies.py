from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.Proxy], tags=["proxies", "crud"])
async def read_proxies(
    filters: filters.ProxyFilter = FilterDepends(filters.ProxyFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_proxies_paged(db, filters)


@router.get("/filters", response_model=list[schemas.Filter], tags=["proxies", "crud"])
async def proxys_filters(
    filters: filters.ProxyFilter = FilterDepends(filters.ProxyFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_proxy_filters(db, filters)


@router.get("/{proxy_id}", response_model=schemas.Proxy | None, tags=["proxies", "crud"])
async def read_proxy(
    proxy_id: str,
    user: Annotated[models.User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_proxy(db, proxy_id)


@router.post("/", response_model=schemas.Proxy, tags=["proxies", "crud"])
async def create_proxy(
    proxy: schemas.ProxyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.create_proxy(db=db, proxy=proxy)


@router.put("/{proxy_id}", response_model=schemas.Proxy, tags=["proxies", "crud"])
async def update_proxy(
    proxy_id: str,
    proxy: schemas.ProxyUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.update_proxy(db=db, proxy_id=proxy_id, proxy_update=proxy)
