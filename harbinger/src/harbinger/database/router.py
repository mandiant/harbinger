# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import collections
import io
import uuid
import zipfile
from fastapi_filter import FilterDepends
from harbinger.database import filters
import yaml
from graphlib import TopologicalSorter, CycleError
import json
from typing import Optional, Tuple
from fastapi.responses import StreamingResponse
from harbinger.worker.workflows import (
    RunPlaybook,
    RunC2Job,
    ParseFile,
    CreateTimeline,
    SyncAll,
    CreateSummaries,
    CreateC2ImplantSuggestion,
    CreateDomainSuggestion,
    CreateFileSuggestion,
    CreateChecklist,
    PlaybookDetectionRisk,
    PrivEscSuggestions,
)
from harbinger.connectors.socks.workflows import RunSocks, RunWindowsSocks
from harbinger.connectors.workflows import C2ServerCommand
from pydantic import UUID4
from harbinger.database.redis_pool import redis_no_decode as redis
import harbinger.proto.v1.messages_pb2 as messages_pb2
import sqlalchemy.exc
from harbinger.config import get_settings
from harbinger.database.crud import get_user_db
from harbinger.database.database import SessionLocal
from harbinger.database.users import (
    current_active_user,
    get_redis_strategy,
    get_redis_strategy,
    get_user_manager,
)
from harbinger.job_templates.schemas import Arguments
from pydantic_core import ValidationError
from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi_pagination import Page, add_pagination
from google.protobuf.json_format import MessageToJson
from harbinger.graph import crud as graph_crud
from harbinger.graph.database import get_async_neo4j_session_context
from sqlalchemy.ext.asyncio import AsyncSession
import yaml
import jsonref
from harbinger.files.client import download_file
from harbinger.worker.client import get_client
from harbinger.config import constants
from . import crud, models, schemas, progress_bar
from temporalio import exceptions
import logging
from paramiko import SSHClient, AutoAddPolicy, AuthenticationException, SSHException, RSAKey
import re
from typing import AsyncGenerator

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

settings = get_settings()


router = APIRouter()


def get_db(request: Request) -> AsyncSession:
    return request.state.db  # type: ignore


@router.get(
    "/domains/",
    response_model=Page[schemas.Domain],
    tags=["crud", "domains"],
)
async def list_domains(
    filters: filters.DomainFilter = FilterDepends(filters.DomainFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_domains_paged(db, filters)


@router.get(
    "/domains/filters", response_model=list[schemas.Filter], tags=["domains", "crud"]
)
async def domains_filters(
    filters: filters.DomainFilter = FilterDepends(filters.DomainFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_domains_filters(
        db,
        filters,
    )


@router.get(
    "/domains/{id}",
    response_model=Optional[schemas.Domain],
    tags=["crud", "domains"],
)
async def get_domain(
    id: UUID4,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_domain(id)


@router.post("/domains/", response_model=schemas.Domain, tags=["crud", "domains"])
async def create_domain(
    domains: schemas.DomainCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_domain(db, domains)


@router.put(
    "/domains/{id}",
    response_model=Optional[schemas.Domain],
    tags=["crud", "domains"],
)
async def update_domain(
    id: UUID4,
    domains: schemas.DomainCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_domain(db, id, domains)


@router.get(
    "/passwords/",
    response_model=Page[schemas.Password],
    tags=["passwords", "crud"],
)
async def read_passwords(
    filters: filters.PasswordFilter = FilterDepends(filters.PasswordFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_passwords_paged(db, filters)


@router.post("/passwords/", response_model=schemas.Password, tags=["passwords", "crud"])
async def create_password(
    password: schemas.PasswordCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_or_create_password(
        db=db,
        password=password.password,
        nt_hash=password.nt,
        aes128_key=password.aes128_key,
        aes256_key=password.aes256_key,
    )


@router.get(
    "/kerberos/",
    response_model=Page[schemas.Kerberos],
    tags=["kerberos", "crud"],
)
async def read_kerberos(
    search: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_kerberos_paged(db, search=search)


@router.get(
    "/kerberos/{kerberos_id}",
    response_model=Optional[schemas.Kerberos],
    tags=["kerberos", "crud"],
)
async def get_kerberos(
    kerberos_id: UUID4,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_kerberos(kerberos_id)


@router.get(
    "/credentials/",
    response_model=Page[schemas.Credential],
    tags=["credentials", "crud"],
)
async def read_credentials(
    filters: filters.CredentialFilter = FilterDepends(filters.CredentialFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_credentials_paged(db, filters)


@router.get(
    "/credentials/filters",
    response_model=list[schemas.Filter],
    tags=["credentials", "crud"],
)
async def credentials_filters(
    filters: filters.CredentialFilter = FilterDepends(filters.CredentialFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_credentials_filters(
        db,
        filters,
    )


@router.get(
    "/credentials/{credential_id}",
    response_model=schemas.Credential,
    tags=["credentials", "crud"],
)
async def read_credential(
    credential_id: str,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_credential(credential_id)


@router.post(
    "/credentials/", response_model=schemas.Credential, tags=["credentials", "crud"]
)
async def create_credential(
    credential: schemas.CredentialCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    credential_obj = await crud.create_credential(db=db, credential=credential)
    if credential.mark_owned and credential.domain_id:
        async with get_async_neo4j_session_context() as session:
            name = (
                f"{credential_obj.username}@{credential_obj.domain.long_name}".upper()
            )
            await graph_crud.mark_owned(session, name)

    return credential_obj


@router.get("/proxies/", response_model=Page[schemas.Proxy], tags=["proxies", "crud"])
async def read_proxies(
    filters: filters.ProxyFilter = FilterDepends(filters.ProxyFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_proxies_paged(db, filters)


@router.get(
    "/proxies/filters", response_model=list[schemas.Filter], tags=["proxies", "crud"]
)
async def proxys_filters(
    filters: filters.ProxyFilter = FilterDepends(filters.ProxyFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_proxy_filters(
        db,
        filters,
    )


@router.get(
    "/proxies/{proxy_id}", response_model=schemas.Proxy, tags=["proxies", "crud"]
)
async def read_proxy(
    proxy_id: str,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_proxy(proxy_id)


@router.post("/proxies/", response_model=schemas.Proxy, tags=["proxies", "crud"])
async def create_proxy(
    proxy: schemas.ProxyCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    proxy = await crud.create_proxy(db=db, proxy=proxy)
    return proxy


@router.get(
    "/proxy_jobs/", response_model=Page[schemas.ProxyJob], tags=["proxy_jobs", "crud"]
)
async def read_proxy_jobs(
    filters: filters.SocksJobFilter = FilterDepends(filters.SocksJobFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_proxy_jobs_paged(db, filters)


@router.get(
    "/proxy_jobs/filters", response_model=list[schemas.Filter], tags=["files", "crud"]
)
async def proxy_job_filters(
    filter: filters.SocksJobFilter = FilterDepends(filters.SocksJobFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_socks_job_filters(
        db,
        filter,
    )


@router.put(
    "/proxy_jobs/{job_id}", response_model=schemas.ProxyJob, tags=["proxy_jobs", "crud"]
)
async def update_proxy_job(
    job_id: str,
    job: schemas.ProxyJobCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_proxy_job(db, job_id=job_id, job=job)


@router.get(
    "/proxy_jobs/{job_id}", response_model=schemas.ProxyJob, tags=["proxy_jobs", "crud"]
)
async def get_proxy_job(
    job_id: str,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_proxy_job(job_id=job_id)


@router.post(
    "/proxy_jobs/{job_id}/kill",
    response_model=schemas.ProxyJob,
    tags=["proxy_jobs", "crud"],
)
async def kill_proxy_job(
    job_id: str,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_proxy_job(job_id=job_id)


@router.post(
    "/proxy_jobs/{job_id}/start",
    response_model=schemas.ProxyJob | schemas.ErrorResponse,
    tags=["proxy_jobs", "crud"],
)
async def start_proxy_job(
    job_id: str,
    response: Response,
    user: models.User = Depends(current_active_user),
):
    proxy_job = await crud.get_proxy_job(job_id=job_id)
    if proxy_job and proxy_job.status != schemas.Status.created:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return dict(error="This job cannot be started, the status is not created.")
    if proxy_job and proxy_job.playbook_id is None:
        client = await get_client()
        if (
            proxy_job.socks_server
            and proxy_job.socks_server.operating_system == "linux"
        ):
            await client.start_workflow(
                RunSocks.run,
                schemas.ProxyJob.model_validate(proxy_job),
                id=job_id,
                task_queue=f"socks_jobs",
            )
        elif (
            proxy_job.socks_server
            and proxy_job.socks_server.operating_system == "windows"
        ):
            try:
                await client.start_workflow(
                    RunWindowsSocks.run,
                    schemas.ProxyJob.model_validate(proxy_job),
                    id=job_id,
                    task_queue=f"socks_jobs",
                )
            except exceptions.WorkflowAlreadyStartedError:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return dict(error="Workflow is already started.")

    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return dict(error="This proxy job is a part of a chain, start the chain.")
    return proxy_job


@router.post(
    "/proxy_jobs/{job_id}/clone",
    response_model=schemas.ProxyJob,
    tags=["proxy_jobs", "crud"],
)
async def clone_proxy_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.clone_proxy_job(db, proxy_job_id=job_id)


@router.post(
    "/proxy_jobs/", response_model=schemas.ProxyJob, tags=["proxy_jobs", "crud"]
)
async def create_proxy_job(
    proxy_job: schemas.ProxyJobCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_proxy_job(db=db, proxy_job=proxy_job)


@router.get(
    "/proxy_job_output/",
    response_model=Page[schemas.ProxyJobOutput],
    tags=["proxy_jobs", "crud"],
)
async def read_proxy_job_output(
    job_id: str = "",
    type: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_proxy_job_output_paged(db, job_id=job_id, type=type)


@router.websocket("/proxy_jobs/{job_id}/output")
async def websocket_job_output(job_id: str, websocket: WebSocket):
    cookie = websocket._cookies["fastapiusersauth"]
    strat = get_redis_strategy()
    async with SessionLocal() as session:
        db = await anext(get_user_db(session))
        manager = await anext(get_user_manager(db))
        token = await strat.read_token(cookie, manager)

    if token:
        await websocket.accept()
        pubsub = redis.pubsub(ignore_subscribe_messages=True)
        await pubsub.subscribe(f"proxy_job_stream_{job_id}")

        async def inner():
            async for item in pubsub.listen():
                output_pb2 = messages_pb2.Output()
                output_pb2.ParseFromString(item["data"])
                await websocket.send_text(
                    MessageToJson(
                        output_pb2,
                        preserving_proto_field_name=True,
                        indent=0,
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


@router.get("/files/", response_model=Page[schemas.File], tags=["files", "crud"])
async def read_files(
    file_filter: filters.FileFilter = FilterDepends(filters.FileFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_files_paged(
        db,
        file_filter,
    )


@router.get(
    "/files/filters", response_model=list[schemas.Filter], tags=["files", "crud"]
)
async def file_filters(
    file_filter: filters.FileFilter = FilterDepends(filters.FileFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_file_filters(
        db,
        file_filter,
    )


@router.get("/files/export", response_model=Page[schemas.File], tags=["files", "crud"])
async def export_files(
    file_filter: filters.FileFilter = FilterDepends(filters.FileFilter),
    max_number: int = 10,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    files = await crud.search_files(
        db,
        file_filter,
        limit=max_number,
    )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file in files:
            try:
                data = await download_file(file.path, file.bucket)
                zip_file.writestr(f"{file.id}_{file.filename}", data)
            except:
                pass

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment;filename=files.zip"},
    )


@router.get(
    "/files/{file_id}", response_model=Optional[schemas.File], tags=["files", "crud"]
)
async def read_file(
    file_id: UUID4,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_file(file_id=file_id)


@router.get("/files/{file_id}/download", tags=["files", "crud"])
async def download_file_endpoint(
    file_id: UUID4,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    file = await crud.get_file(file_id=file_id)
    if file:
        data = await download_file(file.path, file.bucket)
        return Response(
            data,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
        )
    response.status_code = status.HTTP_400_BAD_REQUEST
    return dict(error="File could not be found.")


@router.put(
    "/files/{file_id}",
    response_model=Optional[schemas.File],
    tags=["files", "crud"],
)
async def update_file(
    file_id: str,
    file: schemas.FileUpdate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    await crud.update_file_type(db, file_id, file.filetype)
    return await crud.get_file(file_id)


@router.post(
    "/files/{file_id}/parse",
    response_model=Optional[schemas.File],
    tags=["files", "crud"],
)
async def parse_file(
    file_id: str,
    user: models.User = Depends(current_active_user),
):
    file = await crud.get_file(file_id)
    client = await get_client()
    if file:
        client = await get_client()
        await client.start_workflow(
            ParseFile.run,
            file_id,
            id=str(uuid.uuid4()),
            task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
        )

    return file


@router.get(
    "/files/{file_id}/content",
    response_model=Optional[schemas.FileContent],
    tags=["files", "crud"],
)
async def file_content(
    file_id: str,
    response: Response,
    user: models.User = Depends(current_active_user),
):
    file = await crud.get_file(file_id=file_id)
    if file:
        data = await download_file(file.path, file.bucket)
        return schemas.FileContent(text=data.decode("utf-8", "ignore"))
    response.status_code = status.HTTP_400_BAD_REQUEST
    return dict(error="File could not be found.")


@router.get(
    "/playbooks/",
    response_model=Page[schemas.ProxyChain],
    tags=["crud", "playbooks"],
)
async def list_playbooks(
    filters: filters.PlaybookFilter = FilterDepends(filters.PlaybookFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_playbooks_paged(db, filters)


@router.get(
    "/playbooks/filters",
    response_model=list[schemas.Filter],
    tags=["playbooks", "crud"],
)
async def playbook_filters(
    filters: filters.PlaybookFilter = FilterDepends(filters.PlaybookFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_playbooks_filters(
        db,
        filters,
    )


@router.get(
    "/playbooks/{playbook_id}",
    response_model=schemas.ProxyChainGraph,
    tags=["chains", "crud"],
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


@router.post(
    "/playbooks/",
    response_model=schemas.ProxyChain,
    tags=["chains", "crud"],
)
async def create_chain(
    chain: schemas.ProxyChainCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_chain(db, chain)


@router.put(
    "/playbooks/{playbook_id}",
    response_model=schemas.ProxyChain,
    tags=["chains", "crud"],
)
async def update_chain(
    chain: schemas.ProxyChainCreate,
    playbook_id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_chain(db, playbook_id=playbook_id, chain=chain)


@router.post(
    "/playbooks/{playbook_id}/start",
    response_model=schemas.ProxyChain,
    tags=["chains", "crud"],
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
    "/playbooks/{playbook_id}/clone",
    response_model=schemas.ProxyChain,
    tags=["chains", "crud"],
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


_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


# https://stackoverflow.com/a/33300001
def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


# https://stackoverflow.com/a/21048064
def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())


def dict_constructor(loader, node):
    return collections.OrderedDict(loader.construct_pairs(node))


yaml.add_representer(collections.OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)
yaml.add_representer(str, str_presenter)


@router.get(
    "/playbooks/{playbook_id}/template",
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
                    result["args"].append(  # type: ignore
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
                        result["args"].append(  # type: ignore
                            collections.OrderedDict(
                                name=f"file_id{input_file_count}",
                                type="str",
                                default=str(file.id),
                            )
                        )
                        files.append(f"{{{{ file_id{input_file_count} }}}}")
                        input_file_count += 1
                    step_dict["args"].append(
                        collections.OrderedDict(
                            name=f"input_files",
                            value=files,
                        )  # type: ignore
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
        result["args"].append(collections.OrderedDict(name="c2_implant_id", type="str"))  # type: ignore
    if add_proxy_server:
        result["args"].append(collections.OrderedDict(name="socks_server_id", type="str"))  # type: ignore

    result["steps"] = yaml.dump(steps_yaml)
    return schemas.PlaybookTemplateBase(yaml=yaml.dump(result))


@router.websocket("/playbooks/{playbook_id}/events")
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
                            msg_pb2,
                            preserving_proto_field_name=True,
                            indent=0,
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


def parse_tmate_ssh_username(output: str, readonly: bool = False) -> str:
    """
    Parses the tmate SSH connection string from the job output and returns just the username.
    Returns an empty string if the username cannot be found.
    """
    # Regex to capture the username part: ssh -p<port> <username>@...
    username_pattern = r"ssh -p\d+\s+([a-zA-Z0-9_-]+)@"

    if readonly:
        match = re.search(r"ssh session read only: " + username_pattern, output)
    else:
        match = re.search(r"ssh session: " + username_pattern, output)

    if match:
        return match.group(1)  # Return the captured username
    return ""


async def get_db_ws() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_current_active_user(
    websocket: WebSocket,
):
    """
    Authenticates the user using the fastapiusersauth cookie.
    This is a simplified example; a real-world scenario might involve
    more robust token validation and user retrieval.
    """
    try:
        cookie = websocket._cookies.get("fastapiusersauth", None)
        if not cookie:
            logging.warning("Authentication cookie 'fastapiusersauth' not found.")
            await websocket.close(code=1008, reason="Authentication required")
            return
        strat = get_redis_strategy()
        async with SessionLocal() as session:
            db = await anext(get_user_db(session))
            manager = await anext(get_user_manager(db))
            token = await strat.read_token(cookie, manager)

        if not token:
            logging.warning("Invalid or expired authentication token.")
            await websocket.close(code=1008, reason="Authentication failed")
            return None

        logging.info(f"User authenticated successfully for WebSocket.")
        return token

    except Exception as e:
        logging.error(f"Authentication error: {e}")
        await websocket.close(code=1011, reason=f"Authentication error: {e}")
        return None
    
dummy_key = RSAKey.generate(2048)
async def handle_ssh_websocket(
    websocket: WebSocket,
    username: str,
):
    """
    Handles the SSH websocket communication.
    """

    logging.info(f"Attempting SSH connection to {username}@tmate:2200 for user")

    ssh_client = None
    channel = None

    try:
        await websocket.accept()  # Accept connection after successful authentication and details retrieval

        ssh_client = SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())

        try:

            dummy_key_str = io.StringIO()
            dummy_key.write_private_key(dummy_key_str)
            dummy_key_str.seek(0)
            pkey = RSAKey.from_private_key(dummy_key_str)
            logging.info("Generated dummy SSH key for tmate connection attempt.")
        except Exception as e:
            logging.error(f"Failed to generate dummy SSH key for tmate connection: {e}")
            pkey = None # Proceed without it if generation fails, though connection might fail

        ssh_client.connect(
            hostname="tmate",
            port=2200,
            username=username,
            pkey=pkey, # Pass the dummy key to force publickey auth negotiation
            password=None,
            timeout=10,
            compress=True,
            allow_agent=False,  # Disable looking for SSH agent keys
            look_for_keys=False,  # Disable looking for ~/.ssh/id_rsa, etc.
        )
        logging.info(f"SSH connection established to for {username}.")

        channel = ssh_client.invoke_shell(term="xterm", width=80, height=24)
        channel.setblocking(0)  # Make channel non-blocking

        async def ssh_to_websocket():
            while True:
                try:
                    if channel.recv_ready():
                        data = channel.recv(4096).decode("utf-8", errors="ignore")
                        if data:
                            await websocket.send_text(data)
                    else:
                        await asyncio.sleep(0.01)  # Small delay to prevent busy-waiting
                except Exception as e:
                    logging.error(f"Error in ssh_to_websocket for user {username}: {e}")
                    break
            logging.info(f"ssh_to_websocket task finished for user {username}.")

        async def websocket_to_ssh():
            while True:
                try:
                    message = await websocket.receive_text()
                    if message:
                        if message.startswith("RESIZE:"):
                            try:
                                _, cols_str, rows_str = message.split(":")
                                cols = int(cols_str)
                                rows = int(rows_str)
                                channel.resize_pty(width=cols, height=rows)
                                logging.info(
                                    f"Resized PTY to cols={cols}, rows={rows} for user {username}"
                                )
                            except ValueError as ve:
                                logging.warning(
                                    f"Failed to parse resize message: {message} - {ve}"
                                )
                        else:
                            channel.send(message.encode("utf-8"))
                except WebSocketDisconnect:
                    logging.info(
                        f"WebSocket disconnected from client for user {username}."
                    )
                    break
                except Exception as e:
                    logging.error(f"Error in websocket_to_ssh for user {username}: {e}")
                    break
            logging.info(f"websocket_to_ssh task finished for user {username}.")

        await asyncio.gather(ssh_to_websocket(), websocket_to_ssh())

    except AuthenticationException:
        logging.error(
            f"SSH authentication failed for user {username} to {username}@tmate:2200."
        )
        await websocket.send_text(
            "SSH authentication failed. Please check the job output details."
        )
    except SSHException as e:
        logging.error(f"SSH connection or channel error for user {username}: {e}")
        try:
            await websocket.send_text(f"SSH error: {e}")
        except RuntimeError:
            pass  # WebSocket might already be closed
    except Exception as e:
        logging.error(
            f"Unexpected error in SSH connection handler for user {username}: {e}"
        )
        try:
            await websocket.send_text(f"An unexpected error occurred: {e}")
        except RuntimeError:
            pass  # WebSocket might already be closed
    finally:
        if channel:
            channel.close()
            logging.info(f"SSH channel closed for user {username}.")
        if ssh_client:
            ssh_client.close()
            logging.info(f"SSH client closed for user {username}.")
        logging.info(f"WebSocket connection handler finished for user {username}.")


@router.websocket("/ws/ssh/readonly/{job_id}")
async def websocket_ssh_readonly_endpoint(
    websocket: WebSocket,
    job_id: str,
):
    user = await get_current_active_user(websocket)
    if not user:
        return  # get_current_active_user already closed the websocket
    logging.info(
        f"Attempting read-only SSH connection for job_id: {job_id} and user: {user.email}"
    )
    async with SessionLocal() as db:
        job_output = "\n".join(
            [entry.output for entry in await crud.get_proxy_job_output(db, job_id)]
        )
    username = parse_tmate_ssh_username(job_output, readonly=True)
    await handle_ssh_websocket(websocket, username)


@router.websocket("/ws/ssh/interactive/{job_id}")
async def websocket_ssh_interactive_endpoint(
    websocket: WebSocket,
    job_id: str,
):
    user = await get_current_active_user(websocket)
    if not user:
        return  # get_current_active_user already closed the websocket
    logging.info(
        f"Attempting read-only SSH connection for job_id: {job_id} and user: {user.email}"
    )
    async with SessionLocal() as db:
        job_output = "\n".join(
            [entry.output for entry in await crud.get_proxy_job_output(db, job_id)]
        )
    username = parse_tmate_ssh_username(job_output, readonly=False)
    await handle_ssh_websocket(websocket, username)


@router.get("/steps/", response_model=Page[schemas.ChainStep], tags=["chains", "crud"])
async def get_steps(
    playbook_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_chain_steps_paged(db, playbook_id=playbook_id)


@router.delete("/steps/{step_id}", tags=["chains", "crud"])
async def delete_step(
    step_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    step = await crud.get_chain_step_by_id(db, step_id)
    if step:
        playbook_id = step.playbook_id
        await crud.delete_step(db, step_id)
    return ""


@router.post("/steps/", response_model=schemas.ChainStep, tags=["chains", "crud"])
async def add_step(
    step: schemas.ChainStepCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.add_step(db, step)


@router.post(
    "/steps/{step_id}/clone", response_model=schemas.ChainStep, tags=["chains", "crud"]
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
        return dict(error="Could not locate the step to clone.")
    return await crud.clone_chain_step(
        db, step, str(step.playbook_id), update_label=True
    )


@router.put(
    "/steps/{step_id}",
    response_model=Optional[schemas.ChainStep],
    tags=["chains", "crud"],
)
async def update_step(
    step_id: str,
    step: schemas.ChainStepCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_step(db, step_id, step)


@router.get(
    "/step_modifiers/",
    response_model=Page[schemas.PlaybookStepModifier],
    tags=["chains", "crud"],
)
async def get_step_modifiers(
    playbook_step_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_playbook_steps_modifiers_paged(
        db, playbook_step_id=playbook_step_id
    )


@router.delete("/step_modifiers/{step_id}", tags=["chains", "crud"])
async def delete_step_modifier(
    step_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    step = await crud.get_playbook_step_modifier(db, step_id)
    if step:
        await crud.delete_playbook_step_modifier(db, step_id)
    return ""


@router.post(
    "/step_modifiers/",
    response_model=schemas.PlaybookStepModifier,
    tags=["chains", "crud"],
)
async def add_step_modifier(
    step: schemas.PlaybookStepModifierCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_playbook_step_modifier(db, step)


@router.put(
    "/step_modifiers/{step_id}",
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


@router.get(
    "/c2_servers/filters",
    response_model=list[schemas.Filter],
    tags=["c2_servers", "crud"],
)
async def c2_servers_filters(
    filters: filters.C2ServerFilter = FilterDepends(filters.C2ServerFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_servers_filters(
        db,
        filters,
    )


@router.get(
    "/c2_servers/{id}",
    response_model=Optional[schemas.C2Server],
    tags=["crud", "c2_servers"],
)
async def get_c2_server(
    id: UUID4,
    user: models.User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_c2_server(db, id)


@router.get(
    "/c2/servers/",
    response_model=Page[schemas.C2Server],
    tags=["c2", "implants", "crud"],
)
async def read_c2_servers(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_servers_paged(db)


@router.post(
    "/c2/servers/",
    response_model=schemas.C2Server | None,
    tags=["c2", "implants", "crud"],
)
async def create_c2_server(
    server: schemas.C2ServerCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    server = await crud.create_c2_server(db, c2_server=server)
    if not server:
        return None
    command = schemas.C2ServerCommand(
        command=schemas.Command.create, id=server.id, c2_server=server
    )
    client = await get_client()
    await client.start_workflow(
        C2ServerCommand.run,
        command,
        task_queue="c2_server_commands",
        id=str(uuid.uuid4()),
    )
    return server


@router.get(
    "/c2/servers/statistics/",
    response_model=schemas.StatisticsItems,
    tags=["crud", "statistics"],
)
async def get_c2_server_statistics(user: models.User = Depends(current_active_user)):
    return await crud.get_c2_server_statistics()


@router.post(
    "/c2/servers/{server_id}/command",
    tags=["c2", "implants", "crud"],
)
async def c2_server_command(
    server_id: UUID4,
    data: schemas.C2ServerCommand,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    server = await crud.get_c2_server(db, c2_server_id=server_id)
    client = await get_client()
    if data.command == "sync":
        await client.start_workflow(
            SyncAll.run,
            str(server_id),
            task_queue=constants.WORKER_TASK_QUEUE,
            id=str(uuid.uuid4()),
        )
    else:
        data.c2_server = server
        data.id = server_id
        await client.start_workflow(
            C2ServerCommand.run,
            data,
            task_queue="c2_server_commands",
            id=str(uuid.uuid4()),
        )
    return ""


@router.get(
    "/c2/implants/",
    response_model=Page[schemas.C2Implant],
    tags=["c2", "implants", "crud"],
)
async def read_c2_implants(
    implants_filter: filters.ImplantFilter = FilterDepends(filters.ImplantFilter),
    alive_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_implants_paged(
        db,
        implants_filter,
        alive_only,
    )


@router.get(
    "/c2/implants/filters",
    response_model=list[schemas.Filter],
    tags=["c2", "implants", "crud"],
)
async def c2_implant_filters(
    implants_filter: filters.ImplantFilter = FilterDepends(filters.ImplantFilter),
    alive_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_implant_filters(
        db,
        implants_filter,
        alive_only,
    )


@router.get(
    "/c2/implants/{implant_id}",
    response_model=schemas.C2Implant,
    tags=["c2", "implants", "crud"],
)
async def read_c2_implant(
    implant_id: str,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_implant(c2_implant_id=implant_id)


@router.get(
    "/c2/tasks/",
    response_model=Page[schemas.C2Task],
    tags=["c2", "implants", "crud"],
)
async def read_c2_tasks(
    db: AsyncSession = Depends(get_db),
    filters: filters.C2TaskFilter = FilterDepends(filters.C2TaskFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_tasks_paged(db, filters)


@router.get(
    "/c2/tasks/filters",
    response_model=list[schemas.Filter],
    tags=["c2", "implants", "crud"],
)
async def c2_task_filters(
    db: AsyncSession = Depends(get_db),
    filters: filters.C2TaskFilter = FilterDepends(filters.C2TaskFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_task_filters(db, filters)


@router.get(
    "/c2/tasks/{task_id}",
    response_model=schemas.C2Task,
    tags=["c2", "implants", "crud"],
)
async def read_c2_task(
    task_id: str,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_task(c2_task_id=task_id)


@router.get(
    "/c2/output/export",
    tags=["c2", "implants", "crud"],
)
async def export_c2_output(
    db: AsyncSession = Depends(get_db),
    filters: filters.C2OutputFilter = FilterDepends(filters.C2OutputFilter),
    c2_job_id: str = "",
    user: models.User = Depends(current_active_user),
):
    text = []
    for entry in await crud.get_c2_task_output(
        db,
        filters=filters,
        c2_job_id=c2_job_id,
    ):
        text.append(entry.response_text)
    return StreamingResponse(
        io.StringIO("".join(text)),
        media_type="text/plain",
        headers={"Content-Disposition": "attachment;filename=output.txt"},
    )


@router.get(
    "/c2/output/",
    response_model=Page[schemas.C2Output],
    tags=["c2", "implants", "crud"],
)
async def read_c2_output(
    db: AsyncSession = Depends(get_db),
    filters: filters.C2OutputFilter = FilterDepends(filters.C2OutputFilter),
    c2_job_id: str = "",
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_output_paged(
        db,
        filters=filters,
        c2_job_id=c2_job_id,
    )


@router.get(
    "/c2/output/filters",
    response_model=list[schemas.Filter],
    tags=["c2", "implants", "crud"],
)
async def c2_output_filters(
    db: AsyncSession = Depends(get_db),
    filters: filters.C2OutputFilter = FilterDepends(filters.C2OutputFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_output_filters(
        db,
        filters,
    )


@router.get(
    "/c2/output/{id}",
    response_model=Optional[schemas.C2Output],
    tags=["crud", "c2_outputs"],
)
async def get_c2_output(
    id: UUID4,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_output(id)


@router.get(
    "/c2/jobs/",
    response_model=Page[schemas.C2Job],
    tags=["c2", "implants", "crud"],
)
async def read_c2_jobs(
    db: AsyncSession = Depends(get_db),
    filters: filters.C2JobFilter = FilterDepends(filters.C2JobFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_jobs_paged(db, filters)


@router.post(
    "/c2/jobs/",
    response_model=schemas.C2Job,
    tags=["mythic", "implants", "crud"],
)
async def create_c2_job(
    job: schemas.C2JobCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_c2_job(db=db, job=job)


@router.get(
    "/c2/jobs/filters", response_model=list[schemas.Filter], tags=["c2_jobs", "crud"]
)
async def c2_jobs_filters(
    filters: filters.C2JobFilter = FilterDepends(filters.C2JobFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_jobs_filters(
        db,
        filters,
    )


@router.put(
    "/c2/jobs/{job_id}",
    response_model=schemas.C2Job,
    tags=["mythic", "implants", "crud"],
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
    "/c2/jobs/{job_id}",
    response_model=schemas.C2Job,
    tags=["mythic", "implants", "crud"],
)
async def get_c2_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_job(job_id=job_id)


@router.post(
    "/c2/jobs/{job_id}/start",
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
    "/c2/jobs/{job_id}/clone",
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


@router.get("/hosts/", response_model=Page[schemas.Host], tags=["hosts", "crud"])
async def get_hosts(
    db: AsyncSession = Depends(get_db),
    host_filter: filters.HostFilter = FilterDepends(filters.HostFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_hosts_paged(db, host_filter)


@router.get(
    "/hosts/filters", response_model=list[schemas.Filter], tags=["hosts", "crud"]
)
async def host_filters(
    db: AsyncSession = Depends(get_db),
    host_filter: filters.HostFilter = FilterDepends(filters.HostFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_host_filters(db, host_filter)


@router.get("/hosts/{host_id}", response_model=schemas.Host, tags=["hosts", "crud"])
async def get_host(
    host_id: str,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_host(host_id)


@router.put("/hosts/{host_id}", response_model=schemas.Host, tags=["hosts", "crud"])
async def modify_host(
    host_id: str,
    host: schemas.HostCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    try:
        return await crud.update_host(db, host_id, host)
    except sqlalchemy.exc.IntegrityError:
        return Response("This objectid was already assigned to a host", status_code=400)


@router.get(
    "/processes/", response_model=Page[schemas.Process], tags=["process", "crud"]
)
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


@router.get(
    "/processes/numbers/",
    response_model=schemas.ProcessNumbers,
    tags=["process", "crud"],
)
async def get_process_numbers(
    host_id: str = "",
    implant_id: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    result = await crud.get_process_numbers(db, host_id, implant_id)
    return dict(items=result)


@router.get(
    "/job_statistics/",
    response_model=schemas.StatisticsItems,
    tags=["crud", "statistics"],
)
async def get_job_statistics(user: models.User = Depends(current_active_user)):
    return await crud.get_job_statistics()


# Define the Redis Pub/Sub channel the Go service publishes to
REDIS_PUBSUB_CHANNEL = "app_events_stream" # This MUST match the Go app's `redisPubSubChannel`

@router.websocket("/events")
async def websocket_events(
    websocket: WebSocket,
):
    # --- Authentication (from your original code) ---
    # This part remains mostly the same, ensuring the user is authenticated.
    cookie = websocket._cookies.get("fastapiusersauth", None)
    if not cookie:
        logging.warning("Authentication cookie 'fastapiusersauth' not found.")
        await websocket.close(code=1008, reason="Authentication required")
        return

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
    logging.info(f"WebSocket client authenticated and accepted for user with token: {token}")

    # --- Redis Pub/Sub integration ---
    pubsub = redis.pubsub()

    try:
        await pubsub.subscribe(REDIS_PUBSUB_CHANNEL)
        logging.info(f"Subscribed to Redis channel: {REDIS_PUBSUB_CHANNEL}")

        async def redis_listener():
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        # The Go app now sends raw JSON bytes
                        payload_bytes = message["data"]
                        payload_str = payload_bytes.decode('utf-8')

                        # Directly send the JSON string to the WebSocket client
                        await websocket.send_text(payload_str)

            except asyncio.CancelledError:
                logging.info("Redis listener task cancelled.")
            except Exception as e:
                logging.error(f"Error in Redis listener task: {e}")
            finally:
                logging.info("Unsubscribing from Redis Pub/Sub.")
                await pubsub.unsubscribe(REDIS_PUBSUB_CHANNEL)


        listener_task = asyncio.create_task(redis_listener())

        try:
            # Keep the WebSocket open by waiting for messages from the client
            # (e.g., pings, or other client-sent data)
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logging.info("WebSocket disconnected.")
        except Exception as e:
            logging.error(f"Error in WebSocket receive loop: {e}")
        finally:
            listener_task.cancel()
            await listener_task
            logging.info("WebSocket connection closed.")

    except Exception as e:
        logging.error(f"Error setting up Redis Pub/Sub for WebSocket: {e}")
        await websocket.close(code=1011, reason="Internal server error with event system")


@router.get(
    "/implant_statistics/",
    response_model=schemas.StatisticsItems,
    tags=["crud", "statistics"],
)
async def get_implant_statistics(user: models.User = Depends(current_active_user)):
    return await crud.get_implant_statistics()


@router.get(
    "/labels/",
    response_model=Page[schemas.Label],
    tags=["labels", "crud"],
)
async def get_labels(
    db: AsyncSession = Depends(get_db), user: models.User = Depends(current_active_user)
):
    return await crud.get_labels_paged(db)


@router.get(
    "/labels/grouped",
    response_model=list[schemas.LabelView],
    tags=["labels", "crud"],
)
async def get_labels_grouped(
    db: AsyncSession = Depends(get_db), user: models.User = Depends(current_active_user)
):
    return await crud.get_labels_grouped(db)


@router.post("/labels/", response_model=schemas.Label, tags=["labels", "crud"])
async def create_label(
    label: schemas.LabelCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    try:
        return await crud.create_label(db=db, label=label)
    except sqlalchemy.exc.IntegrityError:
        return Response(
            "Label already exists", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


@router.post(
    "/item_label/", response_model=schemas.LabeledItem, tags=["labels", "crud"]
)
async def create_label_mapping(
    label: schemas.LabeledItemCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_label_item(db=db, label=label)


@router.delete("/item_label/", tags=["labels", "crud"])
async def delete_label_mapping(
    label: schemas.LabeledItemDelete,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.delete_label_item(db=db, label=label)


@router.get("/label_categories/", response_model=list[str], tags=["labels", "crud"])
async def get_label_categories(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_label_categories(db=db)


@router.post(
    "/create_timeline/",
    response_model=schemas.StatusResponse,
    tags=["timeline", "crud"],
)
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


@router.post(
    "/create_summaries/",
    response_model=schemas.StatusResponse,
    tags=["timeline", "crud"],
)
async def create_summaries(
    user: models.User = Depends(current_active_user),
):
    client = await get_client()
    await client.start_workflow(
        CreateSummaries.run,
        id=str(uuid.uuid4()),
        task_queue=constants.WORKER_TASK_QUEUE,
    )
    return schemas.StatusResponse(message="Scheduled")


@router.get(
    "/timeline/", response_model=Page[schemas.TimeLine], tags=["timeline", "crud"]
)
async def timeline(
    filters: filters.TimeLineFilter = FilterDepends(filters.TimeLineFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_timeline_paged(db, filters=filters)


@router.get(
    "/timeline/filters", response_model=list[schemas.Filter], tags=["timeline", "crud"]
)
async def timeline_filters(
    filters: filters.TimeLineFilter = FilterDepends(filters.TimeLineFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_timeline_filters(
        db,
        filters,
    )


@router.get(
    "/situational_awareness/",
    response_model=Page[schemas.SituationalAwareness],
    tags=["situational_awareness", "crud"],
)
async def list_situational_awareness(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
    filters: filters.SituationalAwarenessFilter = FilterDepends(
        filters.SituationalAwarenessFilter
    ),
):
    return await crud.list_situational_awarenesss_paged(
        db,
        filters=filters,
    )


@router.get(
    "/situational_awareness/filters",
    response_model=list[schemas.Filter],
    tags=["situational_awarenesss", "crud"],
)
async def situational_awarenesss_filters(
    filters: filters.SituationalAwarenessFilter = FilterDepends(
        filters.SituationalAwarenessFilter
    ),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_situational_awarenesss_filters(
        db,
        filters,
    )


@router.post(
    "/situational_awareness/",
    response_model=schemas.SituationalAwareness,
    tags=["situational_awareness", "crud"],
)
async def create_situational_awareness(
    sa: schemas.SituationalAwarenessCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    created, sa_db = await crud.get_or_create_situational_awareness(
        db,
        sa=sa,
    )
    return sa_db


@router.put(
    "/situational_awareness/{sa_id}",
    response_model=Optional[schemas.SituationalAwareness],
    tags=["situational_awareness", "crud"],
)
async def update_situational_awareness(
    sa_id: UUID4,
    sa: schemas.SituationalAwarenessCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    await crud.update_situational_awareness(
        db,
        sa_id=sa_id,
        sa=sa,
    )
    return crud.get_situational_awareness(sa_id=sa_id)


@router.delete(
    "/situational_awareness/{sa_id}",
    tags=["situational_awareness", "crud"],
)
async def delete_situational_awareness(
    sa_id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    await crud.delete_situational_awareness(
        db,
        sa_id=sa_id,
    )
    return "Success"


@router.get(
    "/situational_awareness_statistics/",
    response_model=schemas.StatisticsItems,
    tags=["crud", "statistics"],
)
async def get_sa_statistics(user: models.User = Depends(current_active_user)):
    return await crud.get_sa_statistics()


@router.get(
    "/shares/",
    response_model=Page[schemas.Share],
    tags=["crud", "shares"],
)
async def list_shares(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
    share_filters: filters.ShareFilter = FilterDepends(filters.ShareFilter),
):
    return await crud.list_shares_paged(db, share_filters)


@router.get(
    "/shares/filters",
    response_model=list[schemas.Filter],
    tags=["crud", "shares"],
)
async def shares_filters(
    db: AsyncSession = Depends(get_db),
    share_filters: filters.ShareFilter = FilterDepends(filters.ShareFilter),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_share_filters(db, share_filters)


@router.get(
    "/shares/{share_id}",
    response_model=Optional[schemas.Share],
    tags=["crud", "shares"],
)
async def get_share(
    share_id: UUID4,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_share(share_id)


@router.get(
    "/share_files/",
    response_model=Page[schemas.ShareFile],
    tags=["crud", "share_files"],
)
async def list_share_files(
    filters: filters.ShareFileFilter = FilterDepends(filters.ShareFileFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_share_files_paged(db, filters)


@router.get(
    "/share_files/filters",
    response_model=list[schemas.Filter],
    tags=["share_files", "crud"],
)
async def share_files_filters(
    filters: filters.ShareFileFilter = FilterDepends(filters.ShareFileFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_share_file_filters(
        db,
        filters,
    )


@router.get(
    "/share_files/{id}",
    response_model=Optional[schemas.ShareFile],
    tags=["crud", "share_files"],
)
async def get_share_file(
    id: UUID4,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_share_file(id)


@router.get(
    "/share_statistics/",
    response_model=schemas.StatisticsItems,
    tags=["crud", "statistics"],
)
async def get_share_statistics(user: models.User = Depends(current_active_user)):
    return await crud.get_share_statistics()


@router.get(
    "/hashes/",
    response_model=Page[schemas.Hash],
    tags=["crud", "hashes"],
)
async def get_hashes(db: AsyncSession = Depends(get_db)):
    return await crud.list_hashes_paged(db)


@router.get(
    "/hashes/export",
    tags=["crud", "hashes"],
)
async def export_hashes(db: AsyncSession = Depends(get_db)):
    hashes = await crud.list_hashes(db)
    hashes_dict = {}
    for hash in hashes:
        if hash.type not in hashes_dict:
            hashes_dict[hash.type] = []
        hashes_dict[hash.type].append(hash.hash)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for hash_type, hashes in hashes_dict.items():
            zip_file.writestr(f"{hash_type}.txt", "\n".join(hashes))
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment;filename=hashes.zip"},
    )


@router.get("/hashes/{hash_id}", response_model=schemas.Hash, tags=["crud", "hashes"])
async def get_hash(hash_id: UUID4):
    return await crud.get_hash(hash_id)


@router.get(
    "/parse_results/",
    response_model=Page[schemas.ParseResult],
    tags=["parse_results", "crud"],
)
async def read_parse_results(
    db: AsyncSession = Depends(get_db),
    file_id: UUID4 | None = None,
    c2_task_id: UUID4 | None = None,
    c2_task_output_id: UUID4 | None = None,
    proxy_job_output_id: UUID4 | None = None,
    proxy_job_id: UUID4 | None = None,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_parse_results_paged(
        db,
        file_id=file_id,
        c2_task_id=c2_task_id,
        c2_task_output_id=c2_task_output_id,
        proxy_job_id=proxy_job_id,
        proxy_job_output_id=proxy_job_output_id,
    )


@router.get(
    "/parse_results/{parse_id}",
    response_model=Optional[schemas.ParseResult],
    tags=["parse_results", "crud"],
)
async def get_parse_result(
    parse_id: UUID4,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_parse_result(parse_id)


@router.get(
    "/highlights/",
    response_model=Page[schemas.Highlight],
    tags=["crud", "highlights"],
)
async def list_highlights(
    filters: filters.HighlightFilter = FilterDepends(filters.HighlightFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_highlights_paged(db, filters)


@router.get(
    "/highlights/filters",
    response_model=list[schemas.Filter],
    tags=["highlights", "crud"],
)
async def highlights_filters(
    filters: filters.HighlightFilter = FilterDepends(filters.HighlightFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_highlights_filters(
        db,
        filters,
    )


@router.get(
    "/highlights/{id}",
    response_model=Optional[schemas.Highlight],
    tags=["crud", "highlights"],
)
async def get_highlight(
    id: UUID4,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_highlight(id)


add_pagination(router)


@router.get(
    "/settings/", response_model=list[schemas.Settings], tags=["settings", "crud"]
)
async def get_dynamic_settings(
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_settings(db)


@router.patch(
    "/settings/{setting_id}",
    response_model=str,
    tags=["settings", "crud"],
)
async def save_settings(
    setting_id: UUID4,
    setting: schemas.SettingModify,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    await crud.update_setting(db, setting_id, setting)
    return "ok"


@router.get(
    "/socks/servers/", response_model=Page[schemas.SocksServer], tags=["socks", "crud"]
)
async def list_socks_servers(
    filters: filters.SocksServerFilter = FilterDepends(filters.SocksServerFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.list_socks_servers_paged(db, filters)


@router.get(
    "/socks/servers/filters",
    response_model=list[schemas.Filter],
    tags=["socks", "crud"],
)
async def socks_server_filters(
    filters: filters.SocksServerFilter = FilterDepends(filters.SocksServerFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_socks_server_filters(db, filters)


@router.get(
    "/socks/servers/{server_id}",
    response_model=schemas.SocksServer,
    tags=["socks", "crud"],
)
async def get_socks_server(
    server_id: UUID4,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_socks_server(server_id)


@router.post(
    "/socks/servers/",
    response_model=schemas.SocksServer,
    tags=["socks", "crud"],
)
async def create_socks_server(
    server: schemas.SocksServerCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_socks_server(db, server)


@router.get(
    "/servers/statistics/",
    response_model=schemas.StatisticsItems,
    tags=["crud", "statistics"],
)
async def get_server_statistics(user: models.User = Depends(current_active_user)):
    return await crud.get_c2_server_statistics()


@router.get(
    "/actions/",
    response_model=Page[schemas.Action],
    tags=["crud", "actions"],
)
async def get_actions(
    filters: filters.ActionFilter = FilterDepends(filters.ActionFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_actions_paged(db, filters)


@router.get(
    "/actions/filters", response_model=list[schemas.Filter], tags=["actions", "crud"]
)
async def action_filters(
    filters: filters.ActionFilter = FilterDepends(filters.ActionFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_action_filters(
        db,
        filters,
    )

@router.get(
    "/actions/{id}",
    response_model=Optional[schemas.Action],
    tags=["crud", "actions"],
)
async def get_action(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_action(db, id)


@router.get(
    "/certificate_templates/",
    response_model=Page[schemas.CertificateTemplate],
    tags=["crud", "certificate_templates"],
)
async def get_certificate_templates(
    filters: filters.CertificateTemplateFilter = FilterDepends(
        filters.CertificateTemplateFilter
    ),
    enroll_permissions: str = "",
    owner_permissions: str = "",
    writeowner_permissions: str = "",
    fullcontrol_permissions: str = "",
    writedacl_permissions: str = "",
    writeproperty_permissions: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_certificate_templates_paged(
        db,
        filters,
        enroll_permissions=enroll_permissions,
        owner_permissions=owner_permissions,
        writeowner_permissions=writeowner_permissions,
        fullcontrol_permissions=fullcontrol_permissions,
        writedacl_permissions=writedacl_permissions,
        writeproperty_permissions=writeproperty_permissions,
    )


@router.get(
    "/certificate_templates/filters",
    response_model=list[schemas.Filter],
    tags=["certificate_templates", "crud"],
)
async def certificate_templates_filters(
    filters: filters.CertificateTemplateFilter = FilterDepends(
        filters.CertificateTemplateFilter
    ),
    enroll_permissions: str = "",
    owner_permissions: str = "",
    writeowner_permissions: str = "",
    fullcontrol_permissions: str = "",
    writedacl_permissions: str = "",
    writeproperty_permissions: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_certificate_templates_filters(
        db,
        filters,
        enroll_permissions=enroll_permissions,
        owner_permissions=owner_permissions,
        writeowner_permissions=writeowner_permissions,
        fullcontrol_permissions=fullcontrol_permissions,
        writedacl_permissions=writedacl_permissions,
        writeproperty_permissions=writeproperty_permissions,
    )


@router.get(
    "/certificate_templates/{id}",
    response_model=Optional[schemas.CertificateTemplate],
    tags=["crud", "certificate_templates"],
)
async def get_certificate_template(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_certificate_template(db, id)


@router.get(
    "/certificate_authorities/",
    response_model=Page[schemas.CertificateAuthority],
    tags=["crud", "certificate_authorities"],
)
async def list_certificate_authorities(
    filters: filters.CertificateAuthorityFilter = FilterDepends(
        filters.CertificateAuthorityFilter
    ),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_certificate_authorities_paged(db, filters)


@router.get(
    "/certificate_authorities/filters",
    response_model=list[schemas.Filter],
    tags=["certificate_authorities", "crud"],
)
async def certificate_authorities_filters(
    filters: filters.CertificateAuthorityFilter = FilterDepends(
        filters.CertificateAuthorityFilter
    ),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_certificate_authorities_filters(
        db,
        filters,
    )


@router.get(
    "/certificate_authorities/{id}",
    response_model=Optional[schemas.CertificateAuthority],
    tags=["crud", "certificate_authorities"],
)
async def get_certificate_authoritie(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_certificate_authority(db, id)


@router.get(
    "/issues/",
    response_model=Page[schemas.Issue],
    tags=["crud", "issues"],
)
async def list_issues(
    filters: filters.IssueFilter = FilterDepends(filters.IssueFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_issues_paged(db, filters)


@router.get(
    "/issues/filters", response_model=list[schemas.Filter], tags=["issues", "crud"]
)
async def issues_filters(
    filters: filters.IssueFilter = FilterDepends(filters.IssueFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_issue_filters(
        db,
        filters,
    )


@router.get(
    "/issues/{id}",
    response_model=Optional[schemas.Issue],
    tags=["crud", "issues"],
)
async def get_issue(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_issue(db, id)


@router.post("/issues/", response_model=schemas.IssueCreated, tags=["crud", "issues"])
async def create_issue(
    issue: schemas.IssueCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    _, resp = await crud.create_issue(db, issue)
    return resp


@router.put(
    "/issues/{id}",
    response_model=Optional[schemas.Issue],
    tags=["crud", "issues"],
)
async def update_issue(
    id: UUID4,
    issue: schemas.IssueCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    await crud.update_issue(db, id, issue)
    return await crud.get_issue(db, id)


@router.post(
    "/manual_timeline_tasks/",
    response_model=schemas.ManualTimelineTaskCreated,
    tags=["crud", "manual_timeline_tasks"],
)
async def create_manual_timeline_task(
    manual_timeline_tasks: schemas.ManualTimelineTaskCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.create_manual_timeline_task(db, manual_timeline_tasks)


@router.put(
    "/manual_timeline_tasks/{id}",
    response_model=Optional[schemas.ManualTimelineTask],
    tags=["crud", "manual_timeline_tasks"],
)
async def update_manual_timeline_task(
    id: UUID4,
    manual_timeline_tasks: schemas.ManualTimelineTaskCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_manual_timeline_task(db, id, manual_timeline_tasks)


@router.get(
    "/c2_server_types/",
    response_model=Page[schemas.C2ServerType],
    tags=["crud", "c2_server_types"],
)
async def list_c2_server_types(
    filters: filters.C2ServerTypeFilter = FilterDepends(filters.C2ServerTypeFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_server_types_paged(db, filters)


@router.get(
    "/c2_server_arguments/",
    response_model=Page[schemas.C2ServerArguments],
    tags=["crud", "c2_server_arguments"],
)
async def list_c2_server_argumentss(
    c2_server_type: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_c2_server_arguments_paged(db, c2_server_type)


@router.get(
    "/progress_bars/",
    response_model=list[schemas.ProgressBar],
    tags=["crud", "progress_bar"],
)
async def get_progress_bar(user: models.User = Depends(current_active_user)):
    return await progress_bar.get_progress_bars()


@router.delete(
    "/progress_bars/",
    response_model=schemas.StatusResponse,
    tags=["crud", "progress_bar"],
)
async def clear_progress_bars(user: models.User = Depends(current_active_user)):
    result = await progress_bar.get_progress_bars()
    for e in result:
        await progress_bar.delete_progress_bar(e.id)
    return schemas.StatusResponse(message="Cleared")


@router.get(
    "/suggestions/",
    response_model=Page[schemas.Suggestion],
    tags=["crud", "suggestions"],
)
async def list_suggestions(
    filters: filters.SuggestionFilter = FilterDepends(filters.SuggestionFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_suggestions_paged(db, filters)


@router.get(
    "/suggestions/filters",
    response_model=list[schemas.Filter],
    tags=["suggestions", "crud"],
)
async def suggestions_filters(
    filters: filters.SuggestionFilter = FilterDepends(filters.SuggestionFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_suggestions_filters(
        db,
        filters,
    )


@router.get(
    "/suggestions/{id}",
    response_model=Optional[schemas.Suggestion],
    tags=["crud", "suggestions"],
)
async def get_suggestion(
    id: UUID4,
    user: models.User = Depends(current_active_user),
):
    return await crud.get_suggestion(id)


@router.post(
    "/suggestions/c2_implant",
    response_model=schemas.StatusResponse,
    tags=["crud", "suggestions"],
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
    "/suggestions/domain",
    response_model=schemas.StatusResponse,
    tags=["crud", "suggestions"],
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
    "/suggestions/files",
    response_model=schemas.StatusResponse,
    tags=["crud", "suggestions"],
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
    "/suggestions/checklist",
    response_model=schemas.StatusResponse,
    tags=["crud", "suggestions"],
)
async def create_checklist_suggestion(
    suggestion: schemas.SuggestionsRequest,
    user: models.User = Depends(current_active_user),
):
    client = await get_client()
    await client.start_workflow(
        CreateChecklist.run,
        suggestion,
        id=str(uuid.uuid4()),
        task_queue=constants.WORKER_TASK_QUEUE,
    )
    return schemas.StatusResponse(message="Scheduled")


@router.post(
    "/suggestions/playbook_detection",
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
    "/suggestions/privilege_escalation",
    response_model=schemas.StatusResponse,
    tags=["crud", "suggestions"],
)
async def privilege_escalation_suggestions(
    req: schemas.SuggestionsRequest,
    user: models.User = Depends(current_active_user),
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
    "/suggestions/",
    response_model=schemas.SuggestionCreated,
    tags=["crud", "suggestions"],
)
async def create_suggestion(
    suggestions: schemas.SuggestionCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    _, resp = await crud.create_suggestion(db, suggestions)
    return resp


@router.put(
    "/suggestions/{id}",
    response_model=Optional[schemas.Suggestion],
    tags=["crud", "suggestions"],
)
async def update_suggestion(
    id: UUID4,
    suggestions: schemas.SuggestionCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_suggestion(db, id, suggestions)


@router.get(
    "/checklists/",
    response_model=Page[schemas.Checklist],
    tags=["crud", "checklists"],
)
async def list_checklists(
    filters: filters.ChecklistFilter = FilterDepends(filters.ChecklistFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_checklists_paged(db, filters)


@router.get(
    "/checklists/filters",
    response_model=list[schemas.Filter],
    tags=["checklists", "crud"],
)
async def checklists_filters(
    filters: filters.ChecklistFilter = FilterDepends(filters.ChecklistFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_checklists_filters(
        db,
        filters,
    )


@router.get(
    "/checklists/{id}",
    response_model=Optional[schemas.Checklist],
    tags=["crud", "checklists"],
)
async def get_checklist(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_checklist(db, id)


@router.post(
    "/checklists/", response_model=schemas.ChecklistCreated, tags=["crud", "checklists"]
)
async def create_checklist(
    checklists: schemas.ChecklistCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    _, resp = await crud.create_checklist(db, checklists)
    return resp


@router.put(
    "/checklists/{id}",
    response_model=Optional[schemas.Checklist],
    tags=["crud", "checklists"],
)
async def update_checklist(
    id: UUID4,
    checklists: schemas.ChecklistCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_checklist(db, id, checklists)


@router.get(
    "/objectives/",
    response_model=Page[schemas.Objective],
    tags=["crud", "objectives"],
)
async def list_objectives(
    filters: filters.ObjectivesFilter = FilterDepends(filters.ObjectivesFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_objectives_paged(db, filters)


@router.get(
    "/objectives/filters",
    response_model=list[schemas.Filter],
    tags=["objectives", "crud"],
)
async def objectives_filters(
    filters: filters.ObjectivesFilter = FilterDepends(filters.ObjectivesFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_objectives_filters(
        db,
        filters,
    )


@router.get(
    "/objectives/{id}",
    response_model=Optional[schemas.Objective],
    tags=["crud", "objectives"],
)
async def get_objectives(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_objective(db, id)


@router.post(
    "/objectives/", response_model=schemas.ObjectiveCreated, tags=["crud", "objectives"]
)
async def create_objectives(
    objective: schemas.ObjectiveCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    _, resp = await crud.create_objective(db, objective)
    return resp


@router.put(
    "/objectives/{id}",
    response_model=Optional[schemas.Objective],
    tags=["crud", "objectives"],
)
async def update_objectives(
    id: UUID4,
    objective: schemas.ObjectiveCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.update_objective(db, id, objective)
