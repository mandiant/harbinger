import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config import constants
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.database import filters
from harbinger.worker.client import get_client
from harbinger.worker.workflows import (
    CreateC2ImplantSuggestion,
    CreateDomainSuggestion,
    CreateFileSuggestion,
    PlaybookDetectionRisk,
    PrivEscSuggestions,
)

router = APIRouter()


@router.get("/", response_model=Page[schemas.Suggestion], tags=["crud", "suggestions"])
async def list_suggestions(
    filters: filters.SuggestionFilter = FilterDepends(filters.SuggestionFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_suggestions_paged(db, filters)


@router.get(
    "/filters", response_model=list[schemas.Filter], tags=["suggestions", "crud"]
)
async def suggestions_filters(
    filters: filters.SuggestionFilter = FilterDepends(filters.SuggestionFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_suggestions_filters(db, filters)


@router.get(
    "/{id}", response_model=Optional[schemas.Suggestion], tags=["crud", "suggestions"]
)
async def get_suggestion(id: UUID4, user: models.User = Depends(current_active_user)):
    return await crud.get_suggestion(id)


@router.post(
    "/c2_implant", response_model=schemas.StatusResponse, tags=["crud", "suggestions"]
)
async def create_c2_implant_suggestion(
    suggestion: schemas.C2ImplantSuggestionRequest,
    user: models.User = Depends(current_active_user),
):
    client = await get_client()
    await client.start_workflow(
        CreateC2ImplantSuggestion.run,
        suggestion,
        id=str(uuid.uuid4()),
        task_queue=constants.WORKER_TASK_QUEUE,
    )
    return schemas.StatusResponse(message="Scheduled")


@router.post(
    "/domain", response_model=schemas.StatusResponse, tags=["crud", "suggestions"]
)
async def create_ai_suggestion(
    suggestion: schemas.SuggestionsRequest,
    user: models.User = Depends(current_active_user),
):
    client = await get_client()
    await client.start_workflow(
        CreateDomainSuggestion.run,
        suggestion,
        id=str(uuid.uuid4()),
        task_queue=constants.WORKER_TASK_QUEUE,
    )
    return schemas.StatusResponse(message="Scheduled")


@router.post(
    "/files", response_model=schemas.StatusResponse, tags=["crud", "suggestions"]
)
async def create_file_suggestion(
    suggestion: schemas.SuggestionsRequest,
    user: models.User = Depends(current_active_user),
):
    client = await get_client()
    await client.start_workflow(
        CreateFileSuggestion.run,
        suggestion,
        id=str(uuid.uuid4()),
        task_queue=constants.WORKER_TASK_QUEUE,
    )
    return schemas.StatusResponse(message="Scheduled")


@router.post(
    "/playbook_detection",
    response_model=schemas.StatusResponse,
    tags=["crud", "suggestions"],
)
async def c2_task_detection(
    req: schemas.PlaybookDetectionRiskSuggestion,
    user: models.User = Depends(current_active_user),
):
    client = await get_client()
    await client.start_workflow(
        PlaybookDetectionRisk.run,
        req,
        id=str(uuid.uuid4()),
        task_queue=constants.WORKER_TASK_QUEUE,
    )
    return schemas.StatusResponse(message="Scheduled")


@router.post(
    "/privilege_escalation",
    response_model=schemas.StatusResponse,
    tags=["crud", "suggestions"],
)
async def privilege_escalation_suggestions(
    req: schemas.SuggestionsRequest, user: models.User = Depends(current_active_user)
):
    client = await get_client()
    await client.start_workflow(
        PrivEscSuggestions.run,
        req,
        id=str(uuid.uuid4()),
        task_queue=constants.WORKER_TASK_QUEUE,
    )
    return schemas.StatusResponse(message="Scheduled")


@router.post(
    "/", response_model=schemas.SuggestionCreated, tags=["crud", "suggestions"]
)
async def create_suggestion(
    suggestions: schemas.SuggestionCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    _, resp = await crud.create_suggestion(db, suggestions)
    return resp


@router.put(
    "/{id}", response_model=Optional[schemas.Suggestion], tags=["crud", "suggestions"]
)
async def update_suggestion(
    id: UUID4,
    suggestions: schemas.SuggestionCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_suggestion(db, id, suggestions)
