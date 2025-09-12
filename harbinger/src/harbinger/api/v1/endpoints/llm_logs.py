from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.LlmLog], tags=["crud", "llm_logs"])
async def list_llm_logs(
    filters: filters.LlmLogFilter = FilterDepends(filters.LlmLogFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_llm_logs_paged(db, filters)


@router.get("/filters", response_model=list[schemas.Filter], tags=["llm_logs", "crud"])
async def llm_logs_filters(
    filters: filters.LlmLogFilter = FilterDepends(filters.LlmLogFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_llm_logs_filters(db, filters)


@router.get("/{id}", response_model=schemas.LlmLog | None, tags=["crud", "llm_logs"])
async def get_llm_log(
    id: UUID4,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.get_llm_log(db, id)
