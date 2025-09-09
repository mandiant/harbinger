# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os.path
import uuid

from harbinger.worker.client import get_client
from harbinger.worker.workflows import ParseFile
from harbinger.database.redis_pool import redis
from harbinger.config import get_settings
from harbinger.database import crud, schemas
from harbinger import models
from harbinger.database.users import current_active_user
from fastapi import APIRouter, Depends, Request, UploadFile
from harbinger.files.client import upload_file
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from harbinger.config import constants


settings = get_settings()

router = APIRouter()


def get_db(request: Request):
    return request.state.db


@router.post("/upload_file/", response_model=schemas.File, tags=["files"])
async def create_upload_file(
    file: UploadFile,
    file_type: schemas.FileType | str,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    filename = os.path.basename(file.filename or 'file')
    file_db = await crud.add_file(
        db,
        filename=filename,
        bucket=settings.minio_default_bucket,
        path="",
        filetype=file_type,
    )
    file_id = file_db.id
    path = os.path.join("harbinger", f"{file_id}_{filename}")
    await crud.update_file_path(db, file_id, path)

    await upload_file(path, file.file.read())

    file_db = await crud.get_file(file_id)  # type: ignore
    if file_db:
        client = await get_client()
        await client.start_workflow(
            ParseFile.run,
            str(file_id),
            id=str(uuid.uuid4()),
            task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
        )
    return file_db


@router.post("/upload_files/", tags=["files"])
async def upload_files(
    files: List[UploadFile],
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    for file in files:
        filename = os.path.basename(file.filename or 'file')
        file_db = await crud.add_file(
            db,
            filename=filename,
            bucket=settings.minio_default_bucket,
            path="",
        )
        file_id = file_db.id
        path = os.path.join("harbinger", f"{file_id}_{filename}")
        await crud.update_file_path(db, file_id, path)

        await upload_file(path, file.file.read())

        client = await get_client()
        await client.start_workflow(
            ParseFile.run,
            str(file_id),
            id=str(uuid.uuid4()),
            task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
        )

    return "success!"


@router.get("/file_types/", response_model=schemas.FileTypes, tags=["files"])
def file_types(user: models.User = Depends(current_active_user)):
    return {"types": [entry.value for entry in schemas.FileType]}
