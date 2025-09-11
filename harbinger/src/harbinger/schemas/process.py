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

from typing import List

from pydantic import UUID4, AliasChoices, BaseModel, ConfigDict, Field, field_validator


from .label import Label


class ProcessBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    process_id: int | None = Field(
        validation_alias=AliasChoices("process_id", "processid", "pid"), default=None
    )
    architecture: str | None = None
    name: str = Field(validation_alias=AliasChoices("name", "process"))
    user: str | None = Field(
        validation_alias=AliasChoices("user", "process"), default=None
    )
    bin_path: str | None = Field(alias="executablepath", default=None)
    parent_process_id: int | None = Field(
        validation_alias=AliasChoices("parent_process_id", "parentprocessid", "ppid"),
        default=None,
    )
    command_line: str | None = Field(alias="commandline", default=None)
    description: str | None = None
    handle: str | None = None
    host_id: str | str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    number: int | None = None

    @field_validator("architecture")
    def validate_architecture(cls, value):
        if not value:
            return ""
        if "64" in value:
            return "x64"
        return "x32"


class ProcessCreate(ProcessBase):
    pass


class Process(ProcessBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = []


class ProcessMapping(BaseModel):
    name: str
    description: str
    type: str
    tag_id: str
    processes: List[str]


class ProcessNumbers(BaseModel):
    items: list[int]
