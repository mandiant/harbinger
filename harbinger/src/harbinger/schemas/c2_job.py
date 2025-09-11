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

from pydantic import UUID4, BaseModel, ConfigDict


from .file import File
from .label import Label
from .suggestion import SuggestionBaseRequest


class C2Type(str, Enum):
    c2 = "c2"
    proxy = "socks"


class C2JobBase(BaseModel):
    command: str
    arguments: str

    c2_implant_id: UUID4

    playbook_id: UUID4 | str | None = None
    add_labels: list[str] | None = None


class C2JobCreate(C2JobBase):
    input_files: list[str] | None = None


class C2Job(C2JobBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    status: str | None

    message: str | None

    time_created: datetime | None = None
    time_updated: datetime | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None
    labels: List["Label"] | None = None
    input_files: List[File] | None = None


class C2JobDetectionRiskRequest(SuggestionBaseRequest):
    additional_prompt: str = ""
    c2_job_id: UUID4 | str


class C2JobTaskMapping(BaseModel):
    c2_job_id: str | UUID4
    c2_task_id: str | UUID4
