import sqlalchemy.exc
from fastapi import APIRouter, Depends, Response
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger import filters
from harbinger.config.dependencies import current_active_user

router = APIRouter()


@router.get("/", response_model=Page[schemas.Host], tags=["hosts", "crud"])
async def get_hosts(
    db: AsyncSession = Depends(get_db),
    host_filter: filters.HostFilter = FilterDepends(filters.HostFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_hosts_paged(db, host_filter)


@router.get("/filters", response_model=list[schemas.Filter], tags=["hosts", "crud"])
async def host_filters(
    db: AsyncSession = Depends(get_db),
    host_filter: filters.HostFilter = FilterDepends(filters.HostFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_host_filters(db, host_filter)


@router.get("/{host_id}", response_model=schemas.Host, tags=["hosts", "crud"])
async def get_host(host_id: str, user: models.User = Depends(current_active_user)):
    return await crud.get_host(host_id)


@router.put("/{host_id}", response_model=schemas.Host, tags=["hosts", "crud"])
async def modify_host(
    host_id: str,
    host: schemas.HostCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    try:
        return await crud.update_host(db, host_id, host)
    except sqlalchemy.exc.IntegrityError:
        return Response("This objectid was already assigned to a host", status_code=400)
