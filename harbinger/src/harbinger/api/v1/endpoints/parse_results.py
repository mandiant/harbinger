from typing import Optional

from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.config.dependencies import current_active_user

router = APIRouter()


@router.get(
    "/", response_model=Page[schemas.ParseResult], tags=["parse_results", "crud"]
)
async def read_parse_results(
    db: AsyncSession = Depends(get_db),
    file_id: UUID4 | None = None,
    c2_task_id: UUID4 | None = None,
    c2_task_output_id: UUID4 | None = None,
    proxy_job_output_id: UUID4 | None = None,
    proxy_job_id: UUID4 | None = None,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_parse_results_paged(
        db,
        file_id=file_id,
        c2_task_id=c2_task_id,
        c2_task_output_id=c2_task_output_id,
        proxy_job_id=proxy_job_id,
        proxy_job_output_id=proxy_job_output_id,
    )


@router.get(
    "/{parse_id}",
    response_model=Optional[schemas.ParseResult],
    tags=["parse_results", "crud"],
)
async def get_parse_result(
    parse_id: UUID4, user: models.User = Depends(current_active_user)
):
    return await crud.get_parse_result(parse_id)
