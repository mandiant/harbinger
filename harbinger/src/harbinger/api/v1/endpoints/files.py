import io
import uuid
import zipfile
from typing import Optional

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import StreamingResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config import constants
from harbinger.config.dependencies import current_active_user, get_db
from harbinger import filters
from harbinger.config.dependencies import current_active_user
from harbinger.files.client import download_file
from harbinger.worker.client import get_client
from harbinger.worker.workflows import ParseFile

router = APIRouter()


@router.get("/", response_model=Page[schemas.File], tags=["files", "crud"])
async def read_files(
    file_filter: filters.FileFilter = FilterDepends(filters.FileFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_files_paged(db, file_filter)


@router.get("/filters", response_model=list[schemas.Filter], tags=["files", "crud"])
async def file_filters(
    file_filter: filters.FileFilter = FilterDepends(filters.FileFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_file_filters(db, file_filter)


@router.get("/export", response_model=Page[schemas.File], tags=["files", "crud"])
async def export_files(
    file_filter: filters.FileFilter = FilterDepends(filters.FileFilter),
    max_number: int = 10,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    files = await crud.search_files(db, file_filter, limit=max_number)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file in files:
            try:
                data = await download_file(file.path, file.bucket)
                zip_file.writestr(f"{file.id}_{file.filename}", data)
            except:
                pass
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment;filename=files.zip"},
    )


@router.get("/{file_id}", response_model=Optional[schemas.File], tags=["files", "crud"])
async def read_file(file_id: UUID4, user: models.User = Depends(current_active_user)):
    return await crud.get_file(file_id=file_id)


@router.get("/{file_id}/download", tags=["files", "crud"])
async def download_file_endpoint(
    file_id: UUID4,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    file = await crud.get_file(file_id=file_id)
    if file:
        data = await download_file(file.path, file.bucket)
        return Response(
            data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
        )
    response.status_code = status.HTTP_400_BAD_REQUEST
    return dict(error="File could not be found.")


@router.put("/{file_id}", response_model=Optional[schemas.File], tags=["files", "crud"])
async def update_file(
    file_id: str,
    file: schemas.FileUpdate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    await crud.update_file_type(db, file_id, file.filetype)
    return await crud.get_file(file_id)


@router.post(
    "/{file_id}/parse", response_model=Optional[schemas.File], tags=["files", "crud"]
)
async def parse_file(file_id: str, user: models.User = Depends(current_active_user)):
    file = await crud.get_file(file_id)
    client = await get_client()
    if file:
        client = await get_client()
        await client.start_workflow(
            ParseFile.run,
            file_id,
            id=str(uuid.uuid4()),
            task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
        )
    return file


@router.get(
    "/{file_id}/content",
    response_model=Optional[schemas.FileContent],
    tags=["files", "crud"],
)
async def file_content(
    file_id: str, response: Response, user: models.User = Depends(current_active_user)
):
    file = await crud.get_file(file_id=file_id)
    if file:
        data = await download_file(file.path, file.bucket)
        return schemas.FileContent(text=data.decode("utf-8", "ignore"))
    response.status_code = status.HTTP_400_BAD_REQUEST
    return dict(error="File could not be found.")
