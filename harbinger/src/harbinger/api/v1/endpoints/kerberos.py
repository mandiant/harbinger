from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.Kerberos], tags=["kerberos", "crud"])
async def read_kerberos(
    search: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_kerberos_paged(db, search=search)


@router.get(
    "/{kerberos_id}",
    response_model=schemas.Kerberos | None,
    tags=["kerberos", "crud"],
)
async def get_kerberos(
    kerberos_id: UUID4,
    user: Annotated[models.User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_kerberos(db, kerberos_id)
