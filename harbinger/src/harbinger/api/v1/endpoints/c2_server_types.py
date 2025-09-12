from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/",
    response_model=Page[schemas.C2ServerType],
    tags=["crud", "c2_server_types"],
)
async def list_c2_server_types(
    filters: filters.C2ServerTypeFilter = FilterDepends(filters.C2ServerTypeFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_server_types_paged(db, filters)
