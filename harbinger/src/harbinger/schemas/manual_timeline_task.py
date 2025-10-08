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

from .label import Label


class ManualTimelineTaskBase(BaseModel):
    time_created: datetime | None = None
    status: str | None = None
    arguments: str | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None
    command_name: str | None = None
    operator: str | None = None
    output: str | None = None
    hostname: str | None = None
    ai_summary: str | None = ""
    processing_status: str | None = ""

    @field_validator("processing_status")
    @classmethod
    def set_processing_status(cls, processing_status):
        return processing_status or ""


class ManualTimelineTaskCreate(ManualTimelineTaskBase):
    pass


class ManualTimelineTaskCreated(ManualTimelineTaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class ManualTimelineTask(ManualTimelineTaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

    labels: list["Label"] | None = None


ManualTimelineTask.model_rebuild()
