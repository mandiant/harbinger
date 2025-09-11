import json
import uuid

from fastapi import APIRouter, Depends, Response, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from pydantic_core import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config import constants
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.database import filters
from harbinger.job_templates.schemas import Arguments
from harbinger.worker.client import get_client
from harbinger.worker.workflows import RunC2Job

router = APIRouter()


@router.get(
    "/", response_model=Page[schemas.C2Job], tags=["c2", "implants", "crud"]
)
async def read_c2_jobs(
    db: AsyncSession = Depends(get_db),
    filters: filters.C2JobFilter = FilterDepends(filters.C2JobFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_jobs_paged(db, filters)


@router.post("/", response_model=schemas.C2Job, tags=["mythic", "implants", "crud"])
async def create_c2_job(
    job: schemas.C2JobCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_c2_job(db=db, job=job)


@router.get(
    "/filters", response_model=list[schemas.Filter], tags=["c2_jobs", "crud"]
)
async def c2_jobs_filters(
    filters: filters.C2JobFilter = FilterDepends(filters.C2JobFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_jobs_filters(db, filters)


@router.put(
    "/{job_id}", response_model=schemas.C2Job, tags=["mythic", "implants", "crud"]
)
async def update_c2_job(
    job_id: str,
    job: schemas.C2JobCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    try:
        data = json.loads(job.arguments)
        Arguments(**data)
    except json.decoder.JSONDecodeError:
        return Response(
            "Arguments is not valid json",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    except ValidationError as e:
        return Response(
            f"Invalid arguments: {e}", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    return await crud.update_c2_job(db, c2_job_id=job_id, job=job)


@router.get(
    "/{job_id}", response_model=schemas.C2Job, tags=["mythic", "implants", "crud"]
)
async def get_c2_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_job(job_id=job_id)


@router.post(
    "/{job_id}/start",
    response_model=schemas.C2Job,
    tags=["c2", "implants", "crud"],
)
async def start_c2_job(
    job_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    job = await crud.get_c2_job(job_id=job_id)
    if job and job.status != schemas.Status.created:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return dict(error="This job cannot be started, the status is not created.")
    client = await get_client()
    await client.start_workflow(
        RunC2Job.run,
        schemas.C2Job.model_validate(job),
        id=job_id,
        task_queue=constants.WORKER_TASK_QUEUE,
    )
    return await crud.get_c2_job(job_id=job_id)


@router.post(
    "/{job_id}/clone",
    response_model=schemas.C2Job,
    tags=["c2", "implants", "crud"],
)
async def clone_c2_job(
    job_id: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.clone_c2_job(db=db, c2_job_id=job_id)
