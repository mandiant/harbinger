from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/",
    response_model=Page[schemas.ProxyJobOutput],
    tags=["proxy_jobs", "crud"],
)
async def read_proxy_job_output(
    job_id: str = "",
    type: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_proxy_job_output_paged(db, job_id=job_id, type=type)
