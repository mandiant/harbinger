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

from enum import Enum
from typing import Dict, List, Optional, Type
from neo4j import AsyncSession, graph, Query as Neo4jQuery
from harbinger.database import models
from dataclasses import dataclass
from neo4j.exceptions import Neo4jError
import functools


def exception_handler(default):
    def inner(func):
        @functools.wraps(func)
        async def inner2(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Neo4jError:
                return default

        return inner2

    return inner


@exception_handler(default=0)
async def count_users(session: AsyncSession, search: str = "") -> int:
    query = "MATCH (n:User) WHERE n.name IS NOT NULL "
    params: dict = dict()
    if search:
        query += "AND n.name CONTAINS $search "
        params["search"] = search.upper()

    query += "RETURN count(n) as count"
    result = await session.run(query, parameters=params)
    async for graph_entry in result:
        return graph_entry.get("count")  # type: ignore
    return 0


@exception_handler(default=[])
async def get_users(
    session: AsyncSession, search: str, skip: int, limit: int
) -> List[dict]:
    query = "MATCH (n:User) WHERE n.name IS NOT NULL "
    params: dict = dict(skip=skip, limit=limit)
    if search:
        query += "AND n.name CONTAINS $search "
        params["search"] = search.upper()
    query += "RETURN n.name, n.domain, n.objectid, n.owned SKIP $skip LIMIT $limit"
    result = await session.run(query, parameters=params)
    results = []
    async for entry in result:
        entry_dict = dict()
        for key, value in entry.data().items():
            entry_dict[key.replace("n.", "")] = value
        results.append(entry_dict)
    return results


@exception_handler(default=0)
async def count_groups(session: AsyncSession, search: str = "") -> int:
    query = "MATCH (n:Group) WHERE n.name IS NOT NULL "
    params = dict()
    if search:
        query += "AND n.name CONTAINS $search "
        params["search"] = search.upper()
    query += "RETURN count(n) as count"
    result = await session.run(query, parameters=params)
    async for graph_entry in result:
        return graph_entry.get("count") or 0
    return 0


@exception_handler(default=[])
async def get_groups(
    session: AsyncSession, search: str, skip: int, limit: int
) -> List[dict]:
    query = "MATCH (n:Group) WHERE n.name IS NOT NULL "
    params: dict = dict(skip=skip, limit=limit)
    if search:
        query += "AND n.name CONTAINS $search "
        params["search"] = search.upper()
    query += "RETURN n.name, n.domain, n.objectid SKIP $skip LIMIT $limit"
    result = await session.run(query, parameters=params)
    results = []
    async for entry in result:
        entry_dict = dict()
        for key, value in entry.data().items():
            entry_dict[key.replace("n.", "")] = value
        results.append(entry_dict)
    return results


@exception_handler(default=0)
async def count_computers(session: AsyncSession, search: str = "") -> int:
    query = "MATCH (n:Computer) WHERE n.name IS NOT NULL "
    params = dict()
    if search:
        query += "AND n.name CONTAINS $search "
        params["search"] = search.upper()
    query += "RETURN count(n) as count"
    result = await session.run(query, parameters=params)
    async for graph_entry in result:
        return graph_entry.get("count") or 0
    return 0


@exception_handler(default=[])
async def get_computers(
    session: AsyncSession, search: str, skip: int, limit: int
) -> List[dict]:
    query = "MATCH (n:Computer) WHERE n.name IS NOT NULL "
    params = dict(skip=skip, limit=limit, search="")
    if search:
        query += "AND n.name CONTAINS $search "
        params["search"] = search.upper()
    query += "RETURN n.name, n.domain, n.objectid, n.owned SKIP $skip LIMIT $limit"
    result = await session.run(query, parameters=params)
    results = []
    async for entry in result:
        entry_dict = dict()
        for key, value in entry.data().items():
            entry_dict[key.replace("n.", "")] = value
        results.append(entry_dict)
    return results


@exception_handler(default=0)
async def count_domain_controllers(session: AsyncSession, search: str = "") -> int:
    query = "MATCH (g:Group) WHERE g.objectid ENDS WITH '-516' CALL apoc.path.subgraphNodes(g,{relationshipFilter:'<MemberOf', labelFilter: '+Computer', minLevel: 1}) YIELD node AS n "
    parameters = dict()
    if search:
        query += "WITH n WHERE n.name CONTAINS $search "
        parameters["search"] = search.upper()
    query += "RETURN count(n) as count"
    result = await session.run(query, parameters=parameters)
    async for graph_entry in result:
        return graph_entry.get("count") or 0
    return 0


@exception_handler(default=[])
async def get_domain_controllers(
    session: AsyncSession,
    skip: int,
    limit: int,
    search: str = "",
) -> List[dict]:
    parameters: dict = dict(skip=skip, limit=limit)
    query = "MATCH (g:Group) WHERE g.objectid ENDS WITH '-516' CALL apoc.path.subgraphNodes(g,{relationshipFilter:'<MemberOf', labelFilter: '+Computer', minLevel: 1}) YIELD node AS n "
    if search:
        query += "WITH n WHERE n.name CONTAINS $search "
        parameters["search"] = search.upper()
    query += "RETURN n.name, n.domain, n.objectid, n.owned SKIP $skip LIMIT $limit"
    result = await session.run(query, parameters=parameters)
    results = []
    async for entry in result:
        entry_dict = dict()
        for key, value in entry.data().items():
            entry_dict[key.replace("n.", "")] = value
        results.append(entry_dict)
    return results


@exception_handler(default=False)
async def mark_owned(session: AsyncSession, name: str) -> bool:
    try:
        query = "MATCH (n) WHERE n.name=$name SET n.owned=true RETURN n.name"
        result = await session.run(query, parameters=dict(name=name.upper()))
        result_value = False
        async for entry in result:
            result_value = True
        return result_value
    except Neo4jError:
        return False


@exception_handler(default=False)
async def unmark_owned(session: AsyncSession, name: str) -> bool:
    query = "MATCH (n) WHERE n.name=$name SET n.owned=false RETURN n.name"
    result = await session.run(query, parameters=dict(name=name.upper()))
    result_value = False
    async for entry in result:
        result_value = True
    return result_value


@exception_handler(default=False)
async def mark_high_value(session: AsyncSession, name: str) -> bool:
    query = "MATCH (n) WHERE n.name=$name SET n.highvalue=true RETURN n.name"
    result = await session.run(query, parameters=dict(name=name.upper()))
    result_value = False
    async for entry in result:
        result_value = True
    return result_value


@exception_handler(default=False)
async def unmark_high_value(session: AsyncSession, name: str) -> bool:
    query = "MATCH (n) WHERE n.name=$name SET n.highvalue=false RETURN n.name"
    result = await session.run(query, parameters=dict(name=name.upper()))
    result_value = False
    async for entry in result:
        result_value = True
    return result_value


@exception_handler(default=False)
async def add_session(session: AsyncSession, computer: str, name: str) -> bool:
    query = "MATCH (u:User) WHERE u.name=$name OPTIONAL MATCH (c:Computer) WHERE c.name=$computer MERGE (c)-[:HasSession]->(u) return u"
    await session.run(query, parameters=dict(name=name.upper(), computer=computer.upper()))
    return True

class GraphObjects(str, Enum):
    user = "User"
    group = "Group"
    computer = "Computer"
    ou = "OU"
    gpo = "GPO"
    domain = "Domain"


stats_query = "MATCH (o:{object_type}) RETURN count(o) AS count"
user_query = "MATCH (o:User) WHERE NOT o.name ENDS WITH '$' RETURN count(o) as count"


@exception_handler(default=dict(items=[]))
async def get_object_stats(session: AsyncSession) -> dict:
    results = []
    for entry in GraphObjects:
        query = stats_query.format(object_type=entry.value)
        if entry == GraphObjects.user:
            query = user_query
        result = await session.run(query)
        async for graph_entry in result:
            results.append(dict(key=entry.name, value=graph_entry.get("count")))
    return dict(items=results)


domains_query = "MATCH (d:Domain) RETURN d.name as name"
total_query = "MATCH (n:Computer) WHERE n.domain = $domain and n.operatingsystem CONTAINS 'Server' and n.enabled = true return count(n) as count"
admin_servers_query = "MATCH (u:Base {owned: true}) WHERE u.domain = $domain CALL apoc.path.subgraphNodes(u, {relationshipFilter:'>AdminTo|>AllowedToDelegate|>MemberOf|>ReadLAPSPassword', minLevel: 1, labelFilter:'-OU|-GPO|/User|/Computer'}) YIELD node as node UNWIND node as n WITH n WHERE n.enabled = true and 'Computer' in LABELS(n) and n.operatingsystem contains 'Server' and n.domain = $domain return count(n) as count"

@exception_handler(default=dict(items=[]))
async def get_owned_stats(session: AsyncSession) -> dict:
    results = []
    domains = []
    resp = await session.run(domains_query)  # type: ignore
    async for graph_entry in resp:
        domains.append(graph_entry['name'])

    for domain in domains:
        resp = await session.run(total_query, parameters=dict(domain=domain))  # type: ignore
        result = await resp.single()
        if result and result['count']:
            results.append(dict(key=f"{domain} total servers", value=result['count']))

            resp = await session.run(admin_servers_query, parameters=dict(domain=domain))  # type: ignore
            owned_count = await resp.single()
            if owned_count:
                results.append(dict(key=f"{domain} admin servers", value=owned_count['count']))
    return dict(items=results)


class Query:
    query = ""
    result_key = ""
    icon = "person"
    filter_label = ""
    extra_data_key = ""


class GraphQuery:
    query = ""
    icon = "person"
    nodes_key = "nodes"
    edges_key = "relationships"


class OwnedToGroups(Query):
    """List the groups of all owned principals"""

    query = "MATCH (n:User {owned: true}) CALL apoc.path.subgraphNodes(n, {relationshipFilter: '>MemberOf', minLevel: 1}) YIELD node AS u RETURN DISTINCT u;"
    result_key = "u"


class OwnedToAdmin(Query):
    """List the admin privileges of all owned principals"""

    query = "MATCH (n:User {owned: true}) CALL apoc.path.subgraphNodes(n, {relationshipFilter: '>MemberOf|>AdminTo', minLevel: 1}) YIELD node AS u RETURN DISTINCT u;"
    result_key = "u"
    icon = "computer"
    filter_label = "Computer"


class AllPathsToHighValue(GraphQuery):
    """List all paths to high value"""

    icon = "fas fa-crown"
    query = "MATCH (g {highvalue: true}) CALL apoc.path.subgraphAll(g,{relationshipFilter:'<Enroll|<AddMember|<AdminTo|<AllExtendedRights|<AllowedToDelegate|<ForceChangePassword|<GenericAll|<GenericWrite|<GpLink|<MemberOf|<Owns|<ReadLAPSPassword|<WriteDacl|<WriteOwner|<Contains|<HasSession', minLevel: 1}) YIELD nodes, relationships RETURN nodes, relationships"


class AllNodesToHighValue(Query):
    """List all nodes that have paths to high value"""

    icon = "fas fa-crown"
    query = "MATCH (g {highvalue: true}) CALL apoc.path.subgraphNodes(g,{relationshipFilter:'<Enroll|<AddMember|<AdminTo|<AllExtendedRights|<AllowedToDelegate|<ForceChangePassword|<GenericAll|<GenericWrite|<GpLink|<MemberOf|<Owns|<ReadLAPSPassword|<WriteDacl|<WriteOwner|<Contains|<HasSession', minLevel: 1}) YIELD node AS u RETURN DISTINCT u"
    result_key = "u"


class HighValue(Query):
    """List all nodes that are high value"""

    icon = "fas fa-crown"
    query = "MATCH (g {highvalue: true}) RETURN g"
    result_key = "g"


class Kerberoastable(Query):
    """List all nodes that are kerberoastable"""

    icon = "fas fa-crown"
    query = "MATCH (n:User) WHERE n.hasspn=true return n, n.serviceprincipalnames[0] as extra"
    result_key = "n"
    extra_data_key = "extra"


class DomainControllers(Query):
    """List all domain controllers"""

    icon = "computer"
    query = "MATCH (g:Group) WHERE g.objectid ENDS WITH '-516' CALL apoc.path.subgraphNodes(g,{relationshipFilter:'<MemberOf', minLevel: 1}) YIELD node AS u RETURN DISTINCT u"
    result_key = "u"


class SortedKerberoasting(Query):
    """List all kerberoastable accounts and sort by most privileges"""

    icon = "fas fa-crown"
    query = """MATCH (n:User) WHERE n.hasspn=true
CALL apoc.cypher.run("MATCH (u:User {objectid: '"+n.objectid+"'}) CALL apoc.path.subgraphNodes(u, {relationshipFilter: '>Enroll|>AddMember|>AdminTo|>AllExtendedRights|>AllowedToDelegate|>ForceChangePassword|>GenericAll|>GenericWrite|>GpLink|>MemberOf|>Owns|>ReadLAPSPassword|>WriteDacl|>WriteOwner|>Contains|>HasSession', minLevel: 1}) YIELD node AS n1 RETURN DISTINCT n1",null) yield value
RETURN n, count(value) as n2 ORDER by n2 DESC"""
    result_key = "n"
    extra_data_key = "n2"


class AdminPermissions(Query):
    """List the accounts with most direct admin permissions"""

    query = """MATCH (n:User) WHERE n.admincount
CALL apoc.cypher.run("MATCH (u:User {objectid: '"+n.objectid+"'}) CALL apoc.path.subgraphNodes(u, {relationshipFilter: '>AdminTo', minLevel: 1}) YIELD node AS n1 RETURN DISTINCT n1",null) yield value
RETURN n, count(value) as n2 ORDER by n2 DESC"""
    result_key = "n"
    extra_data_key = "n2"


class GraphQueryEnum(str, Enum):
    graph_high_value = "graph_high_value"


class QueryEnum(str, Enum):
    owned_to_groups = "owned_to_groups"
    owned_to_admin = "owned_to_admin"
    all_nodes_to_high_value = "all_nodes_to_high_value"
    Kerberoastable = "kerberoastable"
    domain_controllers = "domain_controllers"
    sorted_kerberoasting = "sorted_kerberoasting"
    high_value = "high_value"
    admin_permissions = "admin_permissions"


QUERY_MAP: Dict[str, Type[Query]] = {
    QueryEnum.owned_to_groups: OwnedToGroups,
    QueryEnum.owned_to_admin: OwnedToAdmin,
    QueryEnum.all_nodes_to_high_value: AllNodesToHighValue,
    QueryEnum.Kerberoastable: Kerberoastable,
    QueryEnum.domain_controllers: DomainControllers,
    QueryEnum.sorted_kerberoasting: SortedKerberoasting,
    QueryEnum.high_value: HighValue,
    QueryEnum.admin_permissions: AdminPermissions,
}

GRAPH_QUERY_MAP: Dict[str, Type[GraphQuery]] = {
    GraphQueryEnum.graph_high_value: AllPathsToHighValue
}


@exception_handler(default=[])
async def run_predefined_query(
    session: AsyncSession, query: str, owned_only: bool = False
) -> List[dict]:
    query_obj = QUERY_MAP[query]
    all_results = []
    result = await session.run(query_obj.query)  # type: ignore
    async for entry in result:
        inner_item = entry.get(query_obj.result_key)
        entry_dict = dict(inner_item)
        entry_dict["labels"] = inner_item.labels
        entry_dict["id"] = inner_item.id
        entry_dict["element_id"] = inner_item.element_id
        if query_obj.extra_data_key:
            entry_dict["extra"] = entry.get(query_obj.extra_data_key)
        if query_obj.filter_label:
            if not query_obj.filter_label in inner_item.labels:
                continue
        if owned_only:
            if not entry_dict.get("owned", False):
                continue
        all_results.append(entry_dict)
    return all_results


@exception_handler(default=[])
async def run_predefined_graph_query(session: AsyncSession, query: str) -> str:
    query_obj = GRAPH_QUERY_MAP[query]
    all_results: list[str] = ["graph LR"]
    result = await session.run(query_obj.query)  # type: ignore
    async for entry in result:
        nodes = entry[query_obj.nodes_key]
        for node in nodes:
            objectid = node.element_id
            name = node["name"]
            if not name:
                name = node["objectid"]
            all_results.append(f'{objectid}("{name}")')
        edges = entry[query_obj.edges_key]
        for edge in edges:
            label = edge.type
            from_id = edge.nodes[0].element_id
            to_id = edge.nodes[1].element_id
            # all_results.append(f"")
            all_results.append(f"{from_id}--{label}-->{to_id}")
    return "\n".join(all_results)


@exception_handler(default=None)
async def get_node(
    session: AsyncSession, objectid: str = "", name: str = ""
) -> Optional[dict]:
    query = ""
    if name:
        query = "MATCH (n {name: $name}) RETURN n"
    elif objectid:
        query = "MATCH (n {objectid: $objectid}) RETURN n"
    else:
        return None
    result = await session.run(query, parameters=dict(objectid=objectid, name=name))
    async for entry in result:
        inner_item = entry.get("n")
        entry_dict = dict(inner_item)
        entry_dict["labels"] = inner_item.labels
        entry_dict["id"] = inner_item.id
        entry_dict["element_id"] = inner_item.element_id
        return entry_dict
    return None


def format_credential(cred: models.Credential) -> str:
    if cred.domain and cred.domain.long_name and not cred.username.endswith("$"):
        return f"{cred.username}@{cred.domain.long_name}".upper()
    return ""


@exception_handler(default=[])
async def get_adminto_for_name(session: AsyncSession, name: str) -> List[dict]:
    query = "MATCH (n:User {name: $name}) CALL apoc.path.subgraphNodes(n, {relationshipFilter: '>MemberOf|>AdminTo', minLevel: 1, labelFilter: '/Computer'}) YIELD node AS u RETURN DISTINCT u;"
    all_results = []
    result = await session.run(query, parameters=dict(name=name))
    async for entry in result:
        inner_item = entry.get("u")
        entry_dict = dict(inner_item)
        entry_dict["labels"] = inner_item.labels
        entry_dict["id"] = inner_item.id
        entry_dict["element_id"] = inner_item.element_id
        if "Computer" in inner_item.labels:
            all_results.append(entry_dict)
    return all_results


def format_node(node: graph.Node) -> dict:
    result = dict(node)
    result["labels"] = node.labels
    result["id"] = int(node.id)
    result["element_id"] = int(node.element_id)
    return result


@dataclass
class Graph:
    nodes: list[dict]
    relationships: list[dict]
    start_node: dict
    end_node: dict


@exception_handler(default=[])
async def get_adminto_graph_for_name(session: AsyncSession, name: str) -> List[Graph]:
    query = "MATCH (n:User {name: $name}) CALL apoc.path.spanningTree(n, {relationshipFilter: '>MemberOf|>AdminTo', minLevel: 1, labelFilter: '/Computer'}) YIELD path RETURN path;"
    all_results = []
    result = await session.run(query, parameters=dict(name=name))
    async for entry in result:
        inner_item: graph.Path = entry.get("path")
        inner_result = Graph(
            nodes=[],
            relationships=[],
            start_node=format_node(inner_item.start_node),
            end_node=format_node(inner_item.end_node),
        )

        for node in inner_item.nodes:
            inner_result.nodes.append(format_node(node))

        for element in inner_item.relationships:
            inner_result.relationships.append(
                dict(
                    source=element.nodes[0].id,  # type: ignore
                    target=element.nodes[1].id,  # type: ignore
                    type=element.type,
                )
            )
        all_results.append(result)
    return all_results


@exception_handler(default={})
async def get_group_membership_for_name(session: AsyncSession, name: str) -> dict:
    query = "MATCH (n:User {name: $name}) CALL apoc.path.spanningTree(n, {relationshipFilter: '>MemberOf', minLevel: 1}) YIELD path RETURN path;"
    nodes = dict()
    relationsips = []
    query_result = await session.run(query, parameters=dict(name=name))
    async for entry in query_result:
        inner_item: graph.Path = entry.get("path")

        for node in inner_item.nodes:
            nodes[node.element_id] = format_node(node)

        for element in inner_item.relationships:
            relationsips.append(
                dict(
                    source=element.nodes[0].id,  # type: ignore
                    target=element.nodes[1].id,  # type: ignore
                    type=element.type,
                )
            )
    result = dict(nodes=list(nodes.values()), relationships=relationsips)
    return result
