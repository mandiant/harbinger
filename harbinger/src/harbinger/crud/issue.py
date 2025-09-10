import uuid
from typing import Optional, Tuple

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from harbinger import models, schemas
from harbinger.database import filters
from harbinger.database.cache import redis_cache_invalidate
from pydantic import UUID4
from sqlalchemy import Select, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from ._common import create_filter_for_column


async def get_issues_paged(
    db: AsyncSession, filters: filters.IssueFilter
) -> Page[models.Issue]:
    q: Select = select(models.Issue)
    q = q.outerjoin(models.Issue.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Issue.id)
    return await paginate(db, q)


async def get_issue_filters(db: AsyncSession, filters: filters.IssueFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Issue.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    for field in ["impact", "exploitability"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Issue, field), field, field
        )
        result.append(res)
    return result


async def get_issue(db: AsyncSession, id: UUID4) -> Optional[models.Issue]:
    return await db.get(models.Issue, id)


async def create_issue(
    db: AsyncSession, issues: schemas.IssueCreate
) -> Tuple[bool, models.Issue]:
    data = issues.model_dump()
    q = insert(models.Issue).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update("issues_name_key", set_=data)
    result = await db.scalars(
        update_stmt.returning(models.Issue),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    return (result.time_updated == None, result)


@redis_cache_invalidate(key_prefix="issue", key_param_name="id")
async def update_issue(
    db: AsyncSession, id: str | uuid.UUID, issue: schemas.IssueCreate
) -> None:
    q = update(models.Issue).where(models.Issue.id == id).values(**issue.model_dump())
    await db.execute(q)
    await db.commit()
