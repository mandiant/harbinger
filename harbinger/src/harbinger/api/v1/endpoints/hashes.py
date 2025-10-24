import io
import zipfile
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fastapi_pagination import Page
from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.Hash], tags=["crud", "hashes"])
async def get_hashes(db: Annotated[AsyncSession, Depends(get_db)], user: models.User = Depends(current_active_user)):
    """
    Get all hashes with pagination.
    """
    return await crud.list_hashes_paged(db)


@router.post("/", response_model=schemas.Hash, status_code=201, tags=["crud", "hashes"])
async def create_hash(
    hash: schemas.HashCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: models.User = Depends(current_active_user),
):
    """
    Create a new hash.
    """
    _, db_hash = await crud.create_hash(db, hash)
    return db_hash


@router.get("/export", tags=["crud", "hashes"])
async def export_hashes(db: Annotated[AsyncSession, Depends(get_db)], user: models.User = Depends(current_active_user)):
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
async def get_hash(
    hash_id: UUID4, db: AsyncSession = Depends(get_db), user: models.User = Depends(current_active_user)
):
    return await crud.get_hash(db, hash_id)


@router.put("/{hash_id}", response_model=schemas.Hash, tags=["crud", "hashes"])
async def update_hash(
    hash_id: UUID4,
    hash: schemas.HashCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: models.User = Depends(current_active_user),
):
    """
    Update a hash.
    """
    _, db_hash = await crud.create_hash(db, hash)
    return db_hash


@router.delete("/{hash_id}", status_code=204, tags=["crud", "hashes"])
async def delete_hash(
    hash_id: UUID4, db: Annotated[AsyncSession, Depends(get_db)], user: models.User = Depends(current_active_user)
):
    """
    Delete a hash.
    """
    await crud.delete_hash(db, hash_id)
    return
