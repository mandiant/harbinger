from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.get("/{id}", response_model=schemas.Issue | None, tags=["crud", "issues"])
async def get_issue(
    id: UUID4,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.get_issue(db, id)


@router.post("/", response_model=schemas.IssueCreated, tags=["crud", "issues"])
async def create_issue(
    issue: schemas.IssueCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    _, resp = await crud.create_issue(db, issue)
    return resp


@router.put("/{id}", response_model=schemas.Issue | None, tags=["crud", "issues"])
async def update_issue(
    id: UUID4,
    issue: schemas.IssueCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    await crud.update_issue(db, id, issue)
    return await crud.get_issue(db, id)
