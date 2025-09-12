from typing import Annotated

from fastapi import APIRouter, Depends
from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user

router = APIRouter()


@router.get(
    "/implant/",
    response_model=schemas.StatisticsItems,
    tags=["crud", "statistics"],
)
async def get_implant_statistics(user: Annotated[models.User, Depends(current_active_user)]):
    return await crud.get_implant_statistics()


@router.get(
    "/job/",
    response_model=schemas.StatisticsItems,
    tags=["crud", "statistics"],
)
async def get_job_statistics(user: Annotated[models.User, Depends(current_active_user)]):
    return await crud.get_job_statistics()


@router.get(
    "/server/",
    response_model=schemas.StatisticsItems,
    tags=["crud", "statistics"],
)
async def get_server_statistics(user: Annotated[models.User, Depends(current_active_user)]):
    return await crud.get_c2_server_statistics()


@router.get(
    "/share/",
    response_model=schemas.StatisticsItems,
    tags=["crud", "statistics"],
)
async def get_share_statistics(user: Annotated[models.User, Depends(current_active_user)]):
    return await crud.get_share_statistics()


@router.get("/sa/", response_model=schemas.StatisticsItems, tags=["crud", "statistics"])
async def get_sa_statistics(user: Annotated[models.User, Depends(current_active_user)]):
    return await crud.get_sa_statistics()
