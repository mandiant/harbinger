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


from datetime import datetime
from enum import Enum
from typing import List

from pydantic import (UUID4, BaseModel, ConfigDict, Field)


from .label import Label


class ProxyStatus(str, Enum):
    connected = "connected"
    disconnected = "disconnected"


class ProxyType(str, Enum):
    socks4 = "socks4"
    socks5 = "socks5"


class ProxyBase(BaseModel):
    host: str = "localhost"
    port: int = Field(
        gt=0, lt=65536, description="The port must be between 1 and 65,535"
    )
    type: ProxyType
    status: ProxyStatus
    note: str | None = None
    remote_hostname: str | None = None
    username: str | None = ""
    password: str | None = ""
    c2_server_id: str | UUID4 | None = None
    internal_id: str | None = None
    c2_implant_id: str | UUID4 | None = None
    c2_task_id: str | UUID4 | None = None

class ProxyCreate(ProxyBase):
    pass

class Proxy(ProxyBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = None

    def to_str(self) -> str:
        return f"{self.type.name} {self.host} {self.port} {self.username or ''} {self.password or ''}".strip()

class ProxyChainBase(BaseModel):
    playbook_name: str | None = None
    description: str | None = None
    playbook_template_id: str | UUID4 | None = None

class ProxyChainCreate(ProxyChainBase):
    pass

class ProxyChain(ProxyChainBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    status: str | None = None
    steps: int | None = None
    completed: int | None = None
    arguments: dict | None = None
    time_created: datetime | None = None
    time_updated: datetime | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None
    suggestion_id: UUID4 | None = None

    labels: List["Label"] | None = None

class ProxyChainGraph(ProxyChain):
    graph: str = ""
    correct: bool = True