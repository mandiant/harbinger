import io
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/export", tags=["c2", "implants", "crud"])
async def export_c2_output(
    db: Annotated[AsyncSession, Depends(get_db)],
    filters: filters.C2OutputFilter = FilterDepends(filters.C2OutputFilter),
    c2_job_id: str = "",
    user: models.User = Depends(current_active_user),
):
    text = []
    for entry in await crud.get_c2_task_output(
        db,
        filters=filters,
        c2_job_id=c2_job_id,
    ):
        text.append(entry.response_text)
    return StreamingResponse(
        io.StringIO("".join(text)),
        media_type="text/plain",
        headers={"Content-Disposition": "attachment;filename=output.txt"},
    )


@router.get("/", response_model=Page[schemas.C2Output], tags=["c2", "implants", "crud"])
async def read_c2_output(
    db: Annotated[AsyncSession, Depends(get_db)],
    filters: filters.C2OutputFilter = FilterDepends(filters.C2OutputFilter),
    c2_job_id: str = "",
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_output_paged(db, filters=filters, c2_job_id=c2_job_id)


@router.get(
    "/filters",
    response_model=list[schemas.Filter],
    tags=["c2", "implants", "crud"],
)
async def c2_output_filters(
    db: Annotated[AsyncSession, Depends(get_db)],
    filters: filters.C2OutputFilter = FilterDepends(filters.C2OutputFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_output_filters(db, filters)


@router.get(
    "/{id}",
    response_model=schemas.C2Output | None,
    tags=["crud", "c2_outputs"],
)
async def get_c2_output(id: UUID4, user: Annotated[models.User, Depends(current_active_user)]):
    return await crud.get_c2_output(id)
