from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.Password], tags=["passwords", "crud"])
async def read_passwords(
    filters: filters.PasswordFilter = FilterDepends(filters.PasswordFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_passwords_paged(db, filters)


@router.post("/", response_model=schemas.Password, tags=["passwords", "crud"])
async def create_password(
    password: schemas.PasswordCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.get_or_create_password(
        db=db,
        password=password.password,
        nt_hash=password.nt,
        aes128_key=password.aes128_key,
        aes256_key=password.aes256_key,
    )
