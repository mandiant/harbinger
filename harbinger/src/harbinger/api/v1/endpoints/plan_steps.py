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


@router.get("/", response_model=Page[schemas.PlanStep], tags=["crud", "plan_steps"])
async def list_plan_steps(
    filters: filters.PlanStepFilter = FilterDepends(filters.PlanStepFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_plan_steps_paged(db, filters)


@router.get(
    "/filters", response_model=list[schemas.Filter], tags=["plan_steps", "crud"]
)
async def plan_steps_filters(
    filters: filters.PlanStepFilter = FilterDepends(filters.PlanStepFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_plan_steps_filters(db, filters)


@router.get(
    "/{id}", response_model=Optional[schemas.PlanStep], tags=["crud", "plan_steps"]
)
async def get_plan_step(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_plan_step(db, id)


@router.post("/", response_model=schemas.PlanStep, tags=["crud", "plan_steps"])
async def create_plan_step(
    plan_steps: schemas.PlanStepCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    _, resp = await crud.create_plan_step(db, plan_steps)
    return resp


@router.put(
    "/{id}", response_model=Optional[schemas.PlanStep], tags=["crud", "plan_steps"]
)
async def update_plan_step(
    id: UUID4,
    plan_step: schemas.PlanStepUpdate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_plan_step(db, id, plan_step)
