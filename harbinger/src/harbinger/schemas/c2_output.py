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

from pydantic import UUID4, AliasChoices, BaseModel, ConfigDict, Field, field_validator


from .c2_task import C2TaskBase
from .file_list import FileList
from .label import Label
from .process import ProcessCreate


class C2OutputBase(BaseModel):
    internal_id: str | None = None
    c2_implant_id: UUID4 | str | None = None
    c2_task_id: UUID4 | str | None = None
    c2_server_id: UUID4 | str
    response_text: str | None = Field(
        validation_alias=AliasChoices("response_text", "result"), default=""
    )
    output_type: str | None = Field(
        validation_alias=AliasChoices("output_type", "type"), default=""
    )
    timestamp: datetime | None = None

    @field_validator("response_text")
    @classmethod
    def remove_nullbytes(cls, v: str) -> str:
        if v:
            return v.replace("\x00", "")
        return v


class C2OutputCreate(C2OutputBase):
    response_bytes: bytes | str | None = None
    internal_task_id: str

    bucket: str | None = None
    path: str | None = None

    processes: List[ProcessCreate] | None = []
    file_list: FileList | None = None

    @field_validator("response_bytes")
    @classmethod
    def fix_response_bytes(cls, v: bytes | str | None) -> bytes | None:
        if isinstance(v, str):
            return v.encode("utf-8")
        return v


class C2Output(C2OutputBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = []


class C2OutputCreated(BaseModel):
    created: bool = False
    output: str
    c2_output_id: UUID4 | str
    c2_implant_id: UUID4 | str | None
    highest_process_number: int = 0
    host_id: UUID4 | str | None = None


class C2OutputPlaybook(BaseModel):
    task: C2TaskBase
    output: list[C2OutputCreate]
