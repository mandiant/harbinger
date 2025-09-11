import uuid

from fastapi import APIRouter, Depends

from harbinger import models, schemas
from harbinger.config import constants
from harbinger.config.dependencies import current_active_user
from harbinger.config.dependencies import current_active_user
from harbinger.worker.client import get_client
from harbinger.worker.workflows import CreateSummaries

router = APIRouter()


@router.post("/", response_model=schemas.StatusResponse, tags=["timeline", "crud"])
async def create_summaries(user: models.User = Depends(current_active_user)):
    client = await get_client()
    await client.start_workflow(
        CreateSummaries.run,
        id=str(uuid.uuid4()),
        task_queue=constants.WORKER_TASK_QUEUE,
    )
    return schemas.StatusResponse(message="Scheduled")
