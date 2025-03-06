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

from pydantic import BaseModel


class GraphUser(BaseModel):
    name: str | None = ""
    objectid: str | None = ""
    domain: str | None = ""
    owned: bool | None = None


class GraphUsers(BaseModel):
    items: list[GraphUser]
    total: int
    page: int


class GraphGroup(BaseModel):
    name: str | None = ""
    objectid: str | None = ""
    domain: str | None = ""


class GraphGroups(BaseModel):
    items: list[GraphGroup]
    total: int
    page: int


class GraphComputer(BaseModel):
    name: str | None = ""
    objectid: str | None = ""
    domain: str | None = ""
    owned: bool | None = None


class GraphComputers(BaseModel):
    items: list[GraphComputer]
    total: int
    page: int


class Mark(BaseModel):
    names: list[str]


class MarkResult(BaseModel):
    count: int


class Statistics(BaseModel):
    key: str
    value: int


class StatisticsItems(BaseModel):
    items: list[Statistics]


class Node(BaseModel):
    id: int | None = None
    labels: list[str] | None = None
    name: str | None = None
    highvalue: bool | None = None
    domainsid: str | None = None
    objectid: str | None = None
    domain: str | None = None
    element_id: int | None = None
    admincount: bool | None = None
    distinguishedname: str | None = None
    owned: bool | None = None
    operatingsystem: str | None = None
    unconstraineddelegation: bool | None = None
    enabled: bool | None = None
    pwdlastset: float | None | str = None
    trustedtoauth: bool | None = None
    whencreated: int | float | None | str = None
    serviceprincipalnames: list[str] | None = None
    lastlogontimestamp: float | None | str = None
    extra: str | int | float | bool | None = None


class QueryResult(BaseModel):
    items: list[Node]


class GraphQueryResult(BaseModel):
    graph: str


class Edge(BaseModel):
    target: int
    source: int
    type: str


class PreDefinedQuery(BaseModel):
    name: str
    icon: str
    description: str


class PreDefinedQueries(BaseModel):
    items: list[PreDefinedQuery]


class PerformQuery(BaseModel):
    query: str
