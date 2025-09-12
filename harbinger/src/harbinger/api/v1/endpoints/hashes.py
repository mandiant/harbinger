import io
import zipfile
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fastapi_pagination import Page
from harbinger import crud, schemas
from harbinger.config.dependencies import get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.Hash], tags=["crud", "hashes"])
async def get_hashes(db: Annotated[AsyncSession, Depends(get_db)]):
    return await crud.list_hashes_paged(db)


@router.get("/export", tags=["crud", "hashes"])
async def export_hashes(db: Annotated[AsyncSession, Depends(get_db)]):
    hashes = await crud.list_hashes(db)
    hashes_dict = {}
    for hash in hashes:
        if hash.type not in hashes_dict:
            hashes_dict[hash.type] = []
        hashes_dict[hash.type].append(hash.hash)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for hash_type, hashes in hashes_dict.items():
            zip_file.writestr(f"{hash_type}.txt", "\n".join(hashes))
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment;filename=hashes.zip"},
    )


@router.get("/{hash_id}", response_model=schemas.Hash, tags=["crud", "hashes"])
async def get_hash(hash_id: UUID4):
    return await crud.get_hash(hash_id)
