from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.Process], tags=["process", "crud"])
async def get_processes(
    host_id: str = "",
    implant_id: str = "",
    number: int = 0,
    db: AsyncSession = Depends(get_db),
    parent_process_id: str = "",
    top: bool = False,
    labels_only: bool = False,
    search: str = "",
    user: models.User = Depends(current_active_user),
):
    return await crud.get_processes_paged(
        db,
        host_id,
        implant_id,
        number,
        parent_process_id=parent_process_id,
        only_top_processes=top,
        labels_only=labels_only,
        search=search,
    )


@router.get("/numbers", response_model=schemas.ProcessNumbers, tags=["process", "crud"])
async def get_process_numbers(
    host_id: str = "",
    implant_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    result = await crud.get_process_numbers(db, host_id, implant_id)
    return {"items": result}
