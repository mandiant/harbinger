from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/",
    response_model=Page[schemas.C2ServerArguments],
    tags=["crud", "c2_server_arguments"],
)
async def list_c2_server_argumentss(
    c2_server_type: UUID4,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.get_c2_server_arguments_paged(db, c2_server_type)
