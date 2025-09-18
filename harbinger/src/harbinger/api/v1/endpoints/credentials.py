from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.graph import crud as graph_crud
from harbinger.graph.database import get_async_neo4j_session_context
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.Credential], tags=["credentials", "crud"])
async def read_credentials(
    filters: filters.CredentialFilter = FilterDepends(filters.CredentialFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_credentials_paged(db, filters)


@router.get(
    "/filters",
    response_model=list[schemas.Filter],
    tags=["credentials", "crud"],
)
async def credentials_filters(
    filters: filters.CredentialFilter = FilterDepends(filters.CredentialFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_credentials_filters(db, filters)


@router.get(
    "/{credential_id}",
    response_model=schemas.Credential,
    tags=["credentials", "crud"],
)
async def read_credential(
    credential_id: str,
    user: Annotated[models.User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> models.Credential | None:
    return await crud.get_credential(db, credential_id=credential_id)


@router.post("/", response_model=schemas.Credential, tags=["credentials", "crud"])
async def create_credential(
    credential: schemas.CredentialCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    credential_obj = await crud.create_credential(db=db, credential=credential)
    if credential.mark_owned and credential.domain_id:
        async with get_async_neo4j_session_context() as session:
            name = f"{credential_obj.username}@{credential_obj.domain.long_name}".upper()
            await graph_crud.mark_owned(session, name)
    return credential_obj
