from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger import filters

router = APIRouter()


@router.get(
    "/", response_model=Page[schemas.C2Task], tags=["c2", "implants", "crud"]
)
async def read_c2_tasks(
    db: AsyncSession = Depends(get_db),
    filters: filters.C2TaskFilter = FilterDepends(filters.C2TaskFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_tasks_paged(db, filters)


@router.get(
    "/filters",
    response_model=list[schemas.Filter],
    tags=["c2", "implants", "crud"],
)
async def c2_task_filters(
    db: AsyncSession = Depends(get_db),
    filters: filters.C2TaskFilter = FilterDepends(filters.C2TaskFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_task_filters(db, filters)


@router.get(
    "/{task_id}", response_model=schemas.C2Task, tags=["c2", "implants", "crud"]
)
async def read_c2_task(task_id: str, user: models.User = Depends(current_active_user)):
    return await crud.get_c2_task(c2_task_id=task_id)
