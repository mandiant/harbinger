from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi_pagination import Page
from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/", response_model=Page[schemas.ChainStep], tags=["chains", "crud"])
async def get_steps(
    playbook_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_chain_steps_paged(db, playbook_id=playbook_id)


@router.delete("/{step_id}", tags=["chains", "crud"])
async def delete_step(
    step_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    step = await crud.get_chain_step_by_id(db, step_id)
    if step:
        await crud.delete_step(db, step_id)
    return ""


@router.post("/", response_model=schemas.ChainStep, tags=["chains", "crud"])
async def add_step(
    step: schemas.ChainStepCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.add_step(db, step)


@router.post(
    "/{step_id}/clone",
    response_model=schemas.ChainStep | None,
    tags=["chains", "crud"],
)
async def clone_step(
    response: Response,
    step_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    step = await crud.get_chain_step_by_id(db, step_id)
    if not step:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "Could not locate the step to clone."}
    return await crud.clone_chain_step(
        db,
        step,
        str(step.playbook_id),
        update_label=True,
    )


@router.put(
    "/{step_id}",
    response_model=schemas.ChainStep | None,
    tags=["chains", "crud"],
)
async def update_step(
    step_id: str,
    step: schemas.ChainStepCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.update_step(db, step_id, step)
