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

from pydantic import UUID4, BaseModel, ConfigDict, field_validator

from .credential import Credential
from .file import File
from .label import Label
from .proxy import Proxy
from .socks_server import SocksServer


class ProxyJobBase(BaseModel):
    credential_id: UUID4 | str | None = None
    proxy_id: UUID4 | str | None = None
    command: str = ""
    arguments: str = ""
    socks_server_id: UUID4
    playbook_id: UUID4 | str | None = None
    tmate: bool | None = True
    asciinema: bool | None = True
    proxychains: bool | None = True
    env: str | None = ""

    ai_summary: str | None = ""
    processing_status: str | None = ""

    @field_validator("processing_status")
    @classmethod
    def set_processing_status(cls, processing_status):
        return processing_status or ""


class ProxyJobCreate(ProxyJobBase):
    input_files: list[str] | None = None


class ProxyJobPreview(ProxyJobBase):
    input_files: list[str] | None = None
    model_config = ConfigDict(from_attributes=True)
    socks_server: SocksServer | None = None


class ProxyJob(ProxyJobBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    status: str | None = "created"
    exit_code: int | None = None
    files: list[File] = []
    time_created: datetime | None = None
    time_updated: datetime | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None
    labels: list["Label"] | None = None
    input_files: list[File] | None = None
    proxy: Proxy | None = None
    credential: Credential | None = None
    socks_server_id: UUID4 | None = None
    socks_server: SocksServer | None = None


ProxyJob.model_rebuild()
