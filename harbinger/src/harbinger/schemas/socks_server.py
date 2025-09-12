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
from typing import TYPE_CHECKING

from pydantic import UUID4, BaseModel, ConfigDict

if TYPE_CHECKING:
    from .label import Label


class SocksServerType(str, Enum):
    docker = "docker"
    kubernetes = "kubernetes"
    local = "local"


class ExecutorTypeName(str, Enum):
    linux = "linux"
    windows = "windows"


class SocksServerBase(BaseModel):
    type: SocksServerType
    hostname: str
    operating_system: ExecutorTypeName
    status: str | None = ""


class SocksServerCreate(SocksServerBase):
    id: UUID4 | None = None


class SocksServer(SocksServerBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: list["Label"] | None = []
