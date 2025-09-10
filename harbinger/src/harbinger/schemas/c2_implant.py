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
from typing import List

from pydantic import (UUID4, AliasChoices, BaseModel, ConfigDict, Field,
                      field_validator)


from .label import Label
from .suggestion import SuggestionBaseRequest


class C2ImplantBase(BaseModel):
    c2_server_id: UUID4 | str
    internal_id: str | None = Field(
        validation_alias=AliasChoices("c2_uid", "ID", "internal_id"), default=None
    )
    c2_type: str | None = None
    payload_type: str | None = None
    name: str | None = Field(
        validation_alias=AliasChoices("name", "Name"), default=None
    )
    hostname: str = Field(
        validation_alias=AliasChoices("computer", "hostname", "host", "Hostname"),
        default="",
    )
    description: str | None = Field(
        validation_alias=AliasChoices("description", "note"), default=""
    )
    sleep: int | None = None
    jitter: int | None = None
    os: str | None = Field(validation_alias=AliasChoices("os", "OS"), default=None)
    pid: int | None = Field(validation_alias=AliasChoices("pid", "PID"), default=None)
    architecture: str | None = Field(
        validation_alias=AliasChoices("architecture", "barch", "Arch", "bitness"),
        default="",
    )
    process: str | None = Field(
        validation_alias=AliasChoices("process", "process_name", "Filename"), default=""
    )
    username: str = Field(
        validation_alias=AliasChoices("username", "user", "Username"), default=""
    )
    ip: str | None = Field(validation_alias=AliasChoices("ip", "host"), default="")
    external_ip: str | None = Field(
        validation_alias=AliasChoices("external", "external_ip", "RemoteAddress"),
        default="",
    )
    domain: str | None = None
    last_checkin: datetime | None = Field(
        validation_alias=AliasChoices("last_checkin", "LastCheckin", "last_heartbeat"),
        default=None,
    )
    host_id: UUID4 | str | None = None

    @field_validator("architecture")
    def validate_architecture(cls, value):
        if not value:
            return ""
        if "64" in value:
            return "x64"
        return "x32"

    @field_validator("os")
    def validate_os(cls, value):
        if not value:
            return ""
        if "windows" in value.lower():
            return "windows"
        if "linux" in value.lower():
            return "linux"
        return value

class C2ImplantCreate(C2ImplantBase):
    internal_id: str | None = Field(
        validation_alias=AliasChoices("c2_uid", "ID", "internal_id"), default=None
    )

class C2ImplantUpdate(C2ImplantCreate):
    c2_server_id: UUID4 | str | None = None

class C2Implant(C2ImplantBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = []

class C2ImplantSuggestionRequest(SuggestionBaseRequest):
    c2_implant_id: str
    additional_prompt: str = ''
