import asyncio
import collections
import json

import yaml
from fastapi import (
    APIRouter,
    Depends,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from google.protobuf.json_format import MessageToJson
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from graphlib import TopologicalSorter, CycleError
from typing import Tuple

import harbinger.proto.v1.messages_pb2 as messages_pb2
from harbinger import crud, models, schemas
from harbinger.config import constants
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.crud import get_user_db
from harbinger import filters
from harbinger.database.database import SessionLocal
from harbinger.database.redis_pool import redis_no_decode as redis
from harbinger.database.users import (
    current_active_user,
    get_redis_strategy,
    get_user_manager,
)
from harbinger.worker.client import get_client
from harbinger.worker.workflows import RunPlaybook

router = APIRouter()


async def create_graph(
    playbook_id: str | UUID4,
    db: AsyncSession,
) -> Tuple[str, bool]:
    steps = await crud.get_playbook_steps(db, limit=100000, playbook_id=playbook_id)

    graph = ["graph LR"]
    ts = TopologicalSorter()

    for step in steps:
        label = f"({step.label})"
        if step.proxy_job_id:
            if job := await crud.get_proxy_job(step.proxy_job_id):
                label = f"({step.label}: {job.command})"
        elif step.c2_job_id:
            if job := await crud.get_c2_job(step.c2_job_id):
                label = f"({step.label}:{job.command})"
        if step.depends_on:
            depends_on = step.depends_on.split(",")
            for depends in depends_on:
                graph.append(f"{depends}-->{step.label}")
            ts.add(step.label, *depends_on)

        try:
            schemas.Status(str(step.status))
            graph.append(f"{step.label}{label}:::{step.status}")
        except ValueError:
            graph.append(f"{step.label}{label}:::running")

    acyclic = True
    try:
        ts.prepare()
    except CycleError:
        acyclic = False

    graph.append("classDef completed fill:#21BA45")
    graph.append("classDef running fill:#9370DB")
    graph.append("classDef queued fill:#9370DB")
    graph.append("classDef submitted fill:#9370DB")
    graph.append("classDef error fill:#C10015")

    return "\n".join(graph), acyclic


@router.get("/", response_model=Page[schemas.ProxyChain], tags=["crud", "playbooks"])
async def list_playbooks(
    filters: filters.PlaybookFilter = FilterDepends(filters.PlaybookFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_playbooks_paged(db, filters)


@router.get("/filters", response_model=list[schemas.Filter], tags=["playbooks", "crud"])
async def playbook_filters(
    filters: filters.PlaybookFilter = FilterDepends(filters.PlaybookFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_playbooks_filters(db, filters)


@router.get(
    "/{playbook_id}", response_model=schemas.ProxyChainGraph, tags=["chains", "crud"]
)
async def get_chain(
    playbook_id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    chain = await crud.get_playbook(playbook_id)
    if chain:
        chain.graph, chain.correct = await create_graph(playbook_id=playbook_id, db=db)
        return chain
    return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post("/", response_model=schemas.ProxyChain, tags=["chains", "crud"])
async def create_chain(
    chain: schemas.ProxyChainCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_chain(db, chain)


@router.put(
    "/{playbook_id}", response_model=schemas.ProxyChain, tags=["chains", "crud"]
)
async def update_chain(
    chain: schemas.ProxyChainCreate,
    playbook_id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_chain(db, playbook_id=playbook_id, chain=chain)


@router.post(
    "/{playbook_id}/start", response_model=schemas.ProxyChain, tags=["chains", "crud"]
)
async def start_chain(
    playbook_id: UUID4,
    response: Response,
    user: models.User = Depends(current_active_user),
):
    chain = await crud.get_playbook(playbook_id)
    if chain and chain.status != schemas.Status.created:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return dict(error="This chain cannot be started, the status is not created.")
    client = await get_client()
    await client.start_workflow(
        RunPlaybook.run,
        str(playbook_id),
        id=str(playbook_id),
        task_queue=constants.WORKER_TASK_QUEUE,
    )
    return chain


@router.post(
    "/{playbook_id}/clone", response_model=schemas.ProxyChain, tags=["chains", "crud"]
)
async def clone_chain(
    playbook_id: UUID4,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    chain = await crud.get_playbook(playbook_id)
    if not chain:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return dict(error="Chain could not be found.")
    return await crud.clone_chain(db, chain)


@router.get(
    "/{playbook_id}/template",
    response_model=schemas.PlaybookTemplateBase,
    tags=["chains", "crud"],
)
async def create_template_from_chain(
    playbook_id: UUID4,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    chain = await crud.get_playbook(playbook_id)
    if not chain:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return dict(error="Chain could not be found.")
    result = collections.OrderedDict(
        name=chain.playbook_name, icon="new", add_depends_on="no", args=[], steps=""
    )
    steps = await crud.get_playbook_steps(db, 0, 100000, playbook_id)
    steps_yaml = []
    add_c2_implant = False
    add_proxy_server = False
    input_file_count = 0
    for step in steps:
        step_dict = collections.OrderedDict()
        if step.c2_job_id:
            add_c2_implant = True
            c2_job = await crud.get_c2_job(step.c2_job_id)
            if c2_job:
                step_dict["type"] = schemas.C2Type.c2.value
                step_dict["name"] = c2_job.command
                args = json.loads(c2_job.arguments)
                step_dict["args"] = [
                    collections.OrderedDict(name=key, value=value)
                    for key, value in args.items()
                ]
                step_dict["args"].append(
                    collections.OrderedDict(
                        name="c2_implant_id", value="{{ c2_implant_id }}"
                    )
                )
                if c2_job.input_files:
                    result["args"].append(
                        collections.OrderedDict(
                            name=f"file_id{input_file_count}",
                            type="str",
                            default=str(c2_job.input_files[0].id),
                        )
                    )
                    step_dict["args"].append(
                        collections.OrderedDict(
                            name=f"file_id",
                            value=f"{{{{ file_id{input_file_count} }}}}",
                        )
                    )
                    input_file_count += 1
        elif step.proxy_job_id:
            add_proxy_server = True
            proxy_job = await crud.get_proxy_job(step.proxy_job_id)
            if proxy_job:
                step_dict["type"] = schemas.C2Type.proxy.value
                step_dict["name"] = "custom"
                step_dict["args"] = args = [
                    collections.OrderedDict(name="command", value=proxy_job.command),
                    collections.OrderedDict(
                        name="arguments", value=proxy_job.arguments
                    ),
                ]
                if proxy_job.input_files:
                    files = []
                    for file in proxy_job.input_files:
                        result["args"].append(
                            collections.OrderedDict(
                                name=f"file_id{input_file_count}",
                                type="str",
                                default=str(file.id),
                            )
                        )
                        files.append(f"{{{{ file_id{input_file_count} }}}}")
                        input_file_count += 1
                    step_dict["args"].append(
                        collections.OrderedDict(name=f"input_files", value=files)
                    )
        step_dict["label"] = step.label
        step_dict["depends_on"] = step.depends_on or ""
        if step.step_modifiers:
            modifiers = []
            for modifier in step.step_modifiers:
                modifiers.append(
                    collections.OrderedDict(
                        regex=modifier.regex,
                        input_path=modifier.input_path,
                        output_path=modifier.output_path,
                    )
                )
            step_dict["modifiers"] = modifiers
        steps_yaml.append(step_dict)
    if add_c2_implant:
        result["args"].append(collections.OrderedDict(name="c2_implant_id", type="str"))
    if add_proxy_server:
        result["args"].append(
            collections.OrderedDict(name="socks_server_id", type="str")
        )
    result["steps"] = yaml.dump(steps_yaml)
    return schemas.PlaybookTemplateBase(yaml=yaml.dump(result))


@router.websocket("/{playbook_id}/events")
async def websocket_chain_output(playbook_id: str, websocket: WebSocket):
    cookie = websocket._cookies["fastapiusersauth"]
    strat = get_redis_strategy()
    async with SessionLocal() as session:
        db = await anext(get_user_db(session))
        manager = await anext(get_user_manager(db))
        token = await strat.read_token(cookie, manager)
    if token:
        await websocket.accept()
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"playbook_stream_{playbook_id}")

        async def inner():
            async for item in pubsub.listen():
                if item["type"] != "subscribe":
                    msg_pb2 = messages_pb2.Event()
                    msg_pb2.ParseFromString(item["data"])
                    await websocket.send_text(
                        MessageToJson(
                            msg_pb2, preserving_proto_field_name=True, indent=0
                        )
                    )

        task = asyncio.create_task(inner())
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            task.cancel()
        finally:
            await pubsub.unsubscribe()
