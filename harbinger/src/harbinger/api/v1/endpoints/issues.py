from typing import Optional

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.database import filters
from harbinger.config.dependencies import current_active_user

router = APIRouter()


@router.get("/", response_model=Page[schemas.Issue], tags=["crud", "issues"])
async def list_issues(
    filters: filters.IssueFilter = FilterDepends(filters.IssueFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_issues_paged(db, filters)


@router.get("/filters", response_model=list[schemas.Filter], tags=["issues", "crud"])
async def issues_filters(
    filters: filters.IssueFilter = FilterDepends(filters.IssueFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_issue_filters(db, filters)


@router.get("/{id}", response_model=Optional[schemas.Issue], tags=["crud", "issues"])
async def get_issue(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_issue(db, id)


@router.post("/", response_model=schemas.IssueCreated, tags=["crud", "issues"])
async def create_issue(
    issue: schemas.IssueCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    _, resp = await crud.create_issue(db, issue)
    return resp


@router.put("/{id}", response_model=Optional[schemas.Issue], tags=["crud", "issues"])
async def update_issue(
    id: UUID4,
    issue: schemas.IssueCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    await crud.update_issue(db, id, issue)
    return await crud.get_issue(db, id)
