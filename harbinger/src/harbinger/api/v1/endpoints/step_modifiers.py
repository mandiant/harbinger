from typing import Optional

from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.config.dependencies import current_active_user

router = APIRouter()


@router.get(
    "/", response_model=Page[schemas.PlaybookStepModifier], tags=["chains", "crud"]
)
async def get_step_modifiers(
    playbook_step_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_playbook_steps_modifiers_paged(
        db, playbook_step_id=playbook_step_id
    )


@router.delete("/{step_id}", tags=["chains", "crud"])
async def delete_step_modifier(
    step_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    step = await crud.get_playbook_step_modifier(db, step_id)
    if step:
        await crud.delete_playbook_step_modifier(db, step_id)
    return ""


@router.post("/", response_model=schemas.PlaybookStepModifier, tags=["chains", "crud"])
async def add_step_modifier(
    step: schemas.PlaybookStepModifierCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_playbook_step_modifier(db, step)


@router.put(
    "/{step_id}",
    response_model=Optional[schemas.PlaybookStepModifier],
    tags=["chains", "crud"],
)
async def update_step_modifier(
    step_id: str,
    step: schemas.PlaybookStepModifierCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_playbook_step_modifier(db, step_id, step)
