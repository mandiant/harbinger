from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas

from .label import get_labels_for_q


async def get_c2_output_paged(
    db: AsyncSession,
    filters: filters.C2OutputFilter,
    c2_job_id: str | None = None,
) -> Page[models.C2Output]:
    q: Select = select(models.C2Output).outerjoin(models.C2Output.labels).group_by(models.C2Output.id)
    q = filters.filter(q)
    if c2_job_id:
        q = q.where(models.C2Job.id == c2_job_id)
        q = q.where(models.C2Job.c2_task_id == models.C2Output.c2_task_id)
    q = filters.sort(q)
    return await paginate(db, q)


async def get_c2_output_filters(
    db: AsyncSession,
    filters: filters.C2OutputFilter,
) -> list[schemas.Filter]:
    q: Select = (
        select(func.count(models.C2Output.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    result: list[schemas.Filter] = []
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


async def get_c2_output(
    db: AsyncSession,
    c2_output_id: str | UUID4,
) -> models.C2Output | None:
    return await db.get(models.C2Output, c2_output_id)
