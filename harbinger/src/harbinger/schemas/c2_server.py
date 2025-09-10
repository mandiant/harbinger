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
from typing import List, Optional

from pydantic import (UUID4, BaseModel, ConfigDict)


from .implant import Implant
from .label import Label
from .required_argument import RequiredArgument


class C2ServerStatus(BaseModel):
    status: str = ""
    message: str = ""
    name: str = ""

class C2ServerStatusUpdate(BaseModel):
    status: C2ServerStatus
    c2_server_id: str


class C2ServerTypeBase(BaseModel):
    time_created: datetime | None = None
    time_updated: datetime | None = None
    name: str | None = None
    docker_image: str | None = None
    command: str | None = None

class C2ServerTypeCreate(C2ServerTypeBase):
    id: UUID4 | str | None = None
    icon: str | None = None

class C2ServerType(C2ServerTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

    arguments: list['C2ServerArguments'] | None = None


class C2ServerBase(BaseModel):
    type: str | None = None
    name: str | None = ""
    hostname: str | None = ""
    username: str | None = ""
    port: int | None = None

class C2ServerCreate(C2ServerBase):
    password: str | None = ""
    ca_certificate: str | None = ""
    certificate: str | None = ""
    private_key: str | None = ""
    token: str | None = ""

class C2Server(C2ServerBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = []
    status: List[C2ServerStatus] | None = []

class C2ServerAll(C2ServerBase):
    model_config = ConfigDict(from_attributes=True)
    password: str | None = ""
    ca_certificate: str | None = ""
    certificate: str | None = ""
    private_key: str | None = ""
    token: str | None = ""

class C2ServerArgumentsBase(BaseModel):
    time_created: datetime | None = None
    name: str | None = None
    regex: str | None = None
    default: str | None = None
    error: str | None = None
    type: str | None = None
    c2_server_type_id: str | UUID4 | None = None
    
class C2ServerArgumentsCreate(C2ServerArgumentsBase):
    pass

class C2ServerArgumentsCreated(C2ServerArgumentsBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

class C2ServerArguments(C2ServerArgumentsBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

class Command(str, Enum):
    start = "start"
    stop = "stop"
    restart = "restart"
    create = "create"
    delete = "delete"
    sync = "sync"

class C2ServerCommand(BaseModel):
    name: str = ""
    command: Command
    id: str | UUID4 | None = None
    c2_server: Optional["C2Server"] = None

class C2ServerTypeYaml(BaseModel):
    id: UUID4
    name: str
    docker_image: str
    command: str
    icon_base64: str | None = ''
    required_arguments: List[RequiredArgument]
    implants: List[Implant] = []