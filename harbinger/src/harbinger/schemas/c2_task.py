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

from pydantic import UUID4, AliasChoices, BaseModel, ConfigDict, Field, field_validator

from .label import Label


class C2TaskStatus(BaseModel):
    c2_task_id: str | UUID4
    status: str
    message: str | None = ""


class C2TaskBase(BaseModel):
    internal_id: str | None = None
    c2_implant_id: UUID4 | str | None = None
    c2_server_id: UUID4 | str | None = None
    status: str | None = None
    original_params: str | None = None
    display_params: str | None = None
    time_started: datetime | None = Field(
        validation_alias=AliasChoices(
            "status_timestamp_processing",
            "started_at",
            "time_started",
        ),
        default=None,
    )
    time_completed: datetime | None = Field(
        validation_alias=AliasChoices("timestamp", "finished_at", "time_completed"),
        default=None,
    )
    command_name: str | None = Field(
        validation_alias=AliasChoices("command_name", "command"),
        default="",
    )
    operator: str | None = Field(
        validation_alias=AliasChoices("operator", "user", "created_by"),
        default="",
    )
    ai_summary: str | None = ""
    processing_status: str | None = ""

    @field_validator("processing_status")
    @classmethod
    def set_processing_status(cls, processing_status):
        return processing_status or ""


class C2TaskCreate(C2TaskBase):
    internal_implant_id: str


class C2Task(C2TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    labels: list["Label"] | None = []


C2Task.model_rebuild()
