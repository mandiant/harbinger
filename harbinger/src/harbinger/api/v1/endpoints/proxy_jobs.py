import asyncio
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, WebSocket, WebSocketDisconnect, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from google.protobuf.json_format import MessageToJson
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.connectors.socks.workflows import RunSocks, RunWindowsSocks
from harbinger.crud import get_user_db
from harbinger.database.database import SessionLocal
from harbinger.database.redis_pool import redis_no_decode as redis
from harbinger.database.users import (
    get_redis_strategy,
    get_user_manager,
)
from harbinger.proto.v1 import messages_pb2
from harbinger.worker.client import get_client
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio import exceptions

router = APIRouter()


@router.get("/", response_model=Page[schemas.ProxyJob], tags=["proxy_jobs", "crud"])
async def read_proxy_jobs(
    filters: filters.SocksJobFilter = FilterDepends(filters.SocksJobFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_proxy_jobs_paged(db, filters)


@router.get("/filters", response_model=list[schemas.Filter], tags=["files", "crud"])
async def proxy_job_filters(
    filter: filters.SocksJobFilter = FilterDepends(filters.SocksJobFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_socks_job_filters(db, filter)


@router.put("/{job_id}", response_model=schemas.ProxyJob, tags=["proxy_jobs", "crud"])
async def update_proxy_job(
    job_id: str,
    job: schemas.ProxyJobCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.update_proxy_job(db, job_id=job_id, job=job)


@router.get("/{job_id}", response_model=schemas.ProxyJob, tags=["proxy_jobs", "crud"])
async def get_proxy_job(
    job_id: str,
    user: Annotated[models.User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_proxy_job(db, job_id=job_id)


@router.post(
    "/{job_id}/kill",
    response_model=schemas.ProxyJob,
    tags=["proxy_jobs", "crud"],
)
async def kill_proxy_job(
    job_id: str,
    user: Annotated[models.User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_proxy_job(db, job_id=job_id)


@router.post(
    "/{job_id}/start",
    response_model=schemas.ProxyJob | schemas.ErrorResponse,
    tags=["proxy_jobs", "crud"],
)
async def start_proxy_job(
    job_id: str,
    response: Response,
    user: Annotated[models.User, Depends(current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    proxy_job = await crud.get_proxy_job(db, job_id=job_id)
    if proxy_job and proxy_job.status != schemas.Status.created:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "This job cannot be started, the status is not created."}
    if proxy_job and proxy_job.playbook_id is None:
        client = await get_client()
        if proxy_job.socks_server and proxy_job.socks_server.operating_system == "linux":
            await client.start_workflow(
                RunSocks.run,
                schemas.ProxyJob.model_validate(proxy_job),
                id=job_id,
                task_queue="socks_jobs",
            )
        elif proxy_job.socks_server and proxy_job.socks_server.operating_system == "windows":
            try:
                await client.start_workflow(
                    RunWindowsSocks.run,
                    schemas.ProxyJob.model_validate(proxy_job),
                    id=job_id,
                    task_queue="socks_jobs",
                )
            except exceptions.WorkflowAlreadyStartedError:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return {"error": "Workflow is already started."}
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "This proxy job is a part of a chain, start the chain."}
    return proxy_job


@router.post(
    "/{job_id}/clone",
    response_model=schemas.ProxyJob | None,
    tags=["proxy_jobs", "crud"],
)
async def clone_proxy_job(
    job_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.clone_proxy_job(db, proxy_job_id=job_id)


@router.post("/", response_model=schemas.ProxyJob, tags=["proxy_jobs", "crud"])
async def create_proxy_job(
    proxy_job: schemas.ProxyJobCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.create_proxy_job(db=db, proxy_job=proxy_job)


@router.websocket("/{job_id}/output")
async def websocket_job_output(job_id: str, websocket: WebSocket):
    cookie = websocket._cookies["fastapiusersauth"]
    strat = get_redis_strategy()
    async with SessionLocal() as session:
        db = await anext(get_user_db(session))
        manager = await anext(get_user_manager(db))
        token = await strat.read_token(cookie, manager)
    if not token:
        logging.warning("Invalid or expired authentication token.")
        await websocket.close(code=1008, reason="Invalid or expired token")
        return
    await websocket.accept()
    pubsub = redis.pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe(f"proxy_job_stream_{job_id}")

    async def inner():
        async for item in pubsub.listen():
            output_pb2 = messages_pb2.Output()
            output_pb2.ParseFromString(item["data"])
            await websocket.send_text(
                MessageToJson(output_pb2, preserving_proto_field_name=True, indent=0),
            )

    task = asyncio.create_task(inner())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        task.cancel()
    finally:
        await pubsub.unsubscribe()
