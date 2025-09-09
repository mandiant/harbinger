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

from harbinger.config import get_settings
from harbinger.database import crud, schemas
from harbinger.graph import crud as graph_crud
from harbinger.graph.database import get_async_neo4j_session_context
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from typing import Awaitable, Callable, Optional
from anyio.abc import TaskGroup

import structlog
from harbinger import models
import harbinger.proto.v1.messages_pb2 as messages_pb2
from redis import Redis
from redis import ResponseError


settings = get_settings()

log = structlog.get_logger()

async def create_event_group(redis: Redis, gname: str) -> None:
    try:
        await redis.xgroup_create(name=schemas.Streams.events, groupname=gname, id=0, mkstream=True)
    except ResponseError as e:
        pass


async def read_events(redis: Redis, groupname: str, cb: Callable[[messages_pb2.Event], Awaitable[None]], taskgroup: Optional[TaskGroup] = None, cname: str = settings.hostname):
    """
        Read the events stream and call the cb function for every message.

        groupname: group name, is used by redis to determine which events are already received, group will be created.
        cb: callback function that will take a single Event protobuf message as argument.
        taskgroup: optional taskgroup to start the task in a group.
        cname: consumer name to identify this worker, default is the hostname.
    """
    await create_event_group(redis, groupname)
    log.info(f"Listening on stream: {schemas.Streams.events.value} as: {groupname}")
    while True:
        responses = await redis.xreadgroup(groupname=groupname, consumername=cname, streams={schemas.Streams.events.value: '>'}, block=100)
        for resp in responses or []:
            _, messages = resp
            for _, message in messages:
                try:
                    msg_pb2 = messages_pb2.Event()
                    msg_pb2.ParseFromString(message['message'].encode('utf-8'))
                    if taskgroup:
                        taskgroup.start_soon(cb, msg_pb2)
                    else:
                        await cb(msg_pb2)
                except Exception as e:
                    log.warning(f"Obtained exception trying to parse message: {e}")
        await asyncio.sleep(.5)


async def merge_db_neo4j_host(
    session: AsyncSession,
    host: models.Host,
    domain: schemas.Domain,
    mark_owned: bool = False,
):
    hostname_neo4j = ""
    if host.fqdn:
        hostname_neo4j = host.fqdn
    elif host.name:
        hostname_neo4j = f"{host.name}"
        if domain.long_name:
            hostname_neo4j = f"{hostname_neo4j}.{domain.long_name}"
        elif domain.short_name:
            hostname_neo4j = f"{hostname_neo4j}.{domain.short_name}"

    async with get_async_neo4j_session_context() as graph_session:
        hosts = await graph_crud.get_computers(graph_session, hostname_neo4j, 0, 1)
        if hosts:
            neo4j_host = hosts[0]
            update_host = schemas.HostCreate(
                fqdn=neo4j_host["name"],
                domain=neo4j_host["domain"],
                objectid=neo4j_host["objectid"],
            )
            await crud.update_host(session, host.id, update_host)
            if mark_owned:
                await graph_crud.mark_owned(graph_session, neo4j_host["name"])
