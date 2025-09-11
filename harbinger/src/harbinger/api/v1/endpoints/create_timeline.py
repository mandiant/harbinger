import uuid

from fastapi import APIRouter, Depends

from harbinger import models, schemas
from harbinger.config import constants
from harbinger.config.dependencies import current_active_user
from harbinger.config.dependencies import current_active_user
from harbinger.worker.client import get_client
from harbinger.worker.workflows import CreateTimeline

router = APIRouter()


@router.post("/", response_model=schemas.StatusResponse, tags=["timeline", "crud"])
async def create_timeline(
    create_timeline: schemas.CreateTimeline,
    user: models.User = Depends(current_active_user),
):
    client = await get_client()
    await client.start_workflow(
        CreateTimeline.run,
        create_timeline,
        id=str(uuid.uuid4()),
        task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
    )
    return schemas.StatusResponse(message="Scheduled")
