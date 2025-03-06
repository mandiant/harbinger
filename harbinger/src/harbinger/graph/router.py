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

import sys
from harbinger.database.redis_pool import redis
from harbinger.config import get_settings
from harbinger.database.users import current_active_user
from fastapi import APIRouter, Depends, Response

from harbinger.database import models

from harbinger.graph.database import get_async_neo4j_session_context
from harbinger.graph import crud, schemas
from inspect import getdoc


settings = get_settings()

router = APIRouter()


@router.get("/users/", response_model=schemas.GraphUsers, tags=["graph"])
async def read_graph_users(
    page: int = 1,
    size: int = 10,
    search: str = "",
    user: models.User = Depends(current_active_user),
):
    if size == 0:
        size = sys.maxsize
    async with get_async_neo4j_session_context() as session:
        user_count = await crud.count_users(session, search=search)
        users = await crud.get_users(
            session, search, skip=(page - 1) * size, limit=size
        )
    return dict(
        items=users, total=user_count, page=page, size=size, pages=user_count / size
    )


@router.get("/groups/", response_model=schemas.GraphGroups, tags=["graph"])
async def read_graph_groups(
    page: int = 1,
    size: int = 10,
    search: str = "",
    user: models.User = Depends(current_active_user),
):
    if size == 0:
        size = sys.maxsize
    async with get_async_neo4j_session_context() as session:
        groups_count = await crud.count_groups(session, search=search)
        groups = await crud.get_groups(
            session, search, skip=(page - 1) * size, limit=size
        )
    return dict(
        items=groups,
        total=groups_count,
        page=page,
        size=size,
        pages=groups_count / size,
    )


@router.get("/computers/", response_model=schemas.GraphComputers, tags=["graph"])
async def read_graph_computers(
    page: int = 1,
    size: int = 10,
    search: str = "",
    user: models.User = Depends(current_active_user),
):
    if size == 0:
        size = sys.maxsize
    async with get_async_neo4j_session_context() as session:
        computer_count = await crud.count_computers(session, search=search)
        computers = await crud.get_computers(
            session, search, skip=(page - 1) * size, limit=size
        )
    return dict(
        items=computers,
        total=computer_count,
        page=page,
        size=size,
        pages=computer_count / size,
    )


@router.get("/domain_controllers/", response_model=schemas.GraphComputers, tags=["graph"])
async def read_domain_controllers(
    page: int = 1,
    size: int = 10,
    search: str = '',
    user: models.User = Depends(current_active_user),
):
    if size == 0:
        size = sys.maxsize
    async with get_async_neo4j_session_context() as session:
        computer_count = await crud.count_domain_controllers(session, search=search)
        computers = await crud.get_domain_controllers(
            session, skip=(page - 1) * size, limit=size, search=search,
        )
    return dict(
        items=computers,
        total=computer_count,
        page=page,
        size=size,
        pages=computer_count / size,
    )

@router.post("/mark_owned", response_model=schemas.MarkResult, tags=["graph"])
async def mark_owned(
    owned: schemas.Mark,
    user: models.User = Depends(current_active_user),
):
    count = 0
    async with get_async_neo4j_session_context() as session:
        for name in owned.names:
            if await crud.mark_owned(session, name):
                count += 1

    return dict(count=count)


@router.post("/unmark_owned", response_model=schemas.MarkResult, tags=["graph"])
async def unmark_owned(
    owned: schemas.Mark,
    user: models.User = Depends(current_active_user),
):
    count = 0
    async with get_async_neo4j_session_context() as session:
        for name in owned.names:
            if await crud.unmark_owned(session, name):
                count += 1

    return dict(count=count)


@router.post("/mark_high_value", response_model=schemas.MarkResult, tags=["graph"])
async def mark_high_value(
    high_value: schemas.Mark,
    user: models.User = Depends(current_active_user),
):
    count = 0
    async with get_async_neo4j_session_context() as session:
        for name in high_value.names:
            if await crud.mark_high_value(session, name):
                count += 1

    return dict(count=count)


@router.post("/unmark_high_value", response_model=schemas.MarkResult, tags=["graph"])
async def unmark_high_value(
    high_value: schemas.Mark,
    user: models.User = Depends(current_active_user),
):
    count = 0
    async with get_async_neo4j_session_context() as session:
        for name in high_value.names:
            if await crud.unmark_high_value(session, name):
                count += 1

    return dict(count=count)


@router.get("/stats/", response_model=schemas.StatisticsItems, tags=["graph"])
async def get_stats(
    user: models.User = Depends(current_active_user),
):
    async with get_async_neo4j_session_context() as session:
        result = await crud.get_object_stats(session)

    return result


@router.get("/owned_stats/", response_model=schemas.StatisticsItems, tags=["graph"])
async def get_owned_stats(
    user: models.User = Depends(current_active_user),
):
    async with get_async_neo4j_session_context() as session:
        result = await crud.get_owned_stats(session)
    return result


@router.get(
    "/pre-defined-queries/", response_model=schemas.PreDefinedQueries, tags=["graph"]
)
async def get_pre_defined_queries(
    user: models.User = Depends(current_active_user),
):
    result = []
    for key, value in crud.QUERY_MAP.items():
        result.append(dict(name=key, icon=value.icon, description=getdoc(value)))
    return dict(items=result)


@router.get(
    "/pre-defined-queries-graph/", response_model=schemas.PreDefinedQueries, tags=["graph"]
)
async def get_pre_defined_queries_graph(
    user: models.User = Depends(current_active_user),
):
    result = []
    for key, value in crud.GRAPH_QUERY_MAP.items():
        result.append(dict(name=key, icon=value.icon, description=getdoc(value)))
    return dict(items=result)


@router.get(
    "/pre-defined-queries/{query}", response_model=list[schemas.Node], tags=["graph"]
)
async def pre_defined_query(
    query: str,
    response: Response,
    owned_only: bool = False,
    user: models.User = Depends(current_active_user),
):
    if query not in crud.QUERY_MAP:
        return Response("Query was not found", status_code=400)

    async with get_async_neo4j_session_context() as session:
        return await crud.run_predefined_query(session, query, owned_only=owned_only)


@router.get(
    "/pre-defined-queries-graph/{query}", response_model=schemas.GraphQueryResult, tags=["graph"]
)
async def pre_defined_query_graph(
    query: str,
    response: Response,
    user: models.User = Depends(current_active_user),
):
    if query not in crud.GRAPH_QUERY_MAP:
        return Response("Query was not found", status_code=400)

    async with get_async_neo4j_session_context() as session:
        result = await crud.run_predefined_graph_query(session, query)
        return schemas.GraphQueryResult(graph=result)


@router.get("/nodes/{objectid}", response_model=schemas.Node, tags=["graph"])
async def get_node(
    objectid: str,
    user: models.User = Depends(current_active_user),
):
    async with get_async_neo4j_session_context() as session:
        node = await crud.get_node(session, objectid)
        if not node:
            return Response("Object was not found", status_code=400)
        return node
