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


from datetime import datetime, timedelta

from pydantic import UUID4, BaseModel, ConfigDict

from .label import Label


class PlaybookStepModifierBase(BaseModel):
    regex: str | None = None
    input_path: str
    output_path: str
    output_format: str | None = None
    status: str = ""
    on_error: str = ""
    data: str = ""
    status_message: str = ""


class PlaybookStepModifierCreate(PlaybookStepModifierBase):
    playbook_step_id: UUID4 | str


class PlaybookStepModifier(PlaybookStepModifierBase):
    model_config = ConfigDict(from_attributes=True)
    playbook_step_id: UUID4 | str
    id: UUID4
    time_created: datetime | None = None


class PlaybookStepModifierEntry(PlaybookStepModifierBase):
    # To pass more data during execution of the workflow
    playbook_step_id: UUID4 | str
    proxy_job_id: UUID4 | str | None = None
    c2_job_id: UUID4 | str | None = None


class PlaybookStepBase(BaseModel):
    playbook_id: UUID4 | str | None
    number: int = 0
    label: str | None = ""
    depends_on: str | None = ""
    proxy_job_id: UUID4 | str | None = None
    c2_job_id: UUID4 | str | None = None
    delay: timedelta | None = None
    execute_after: datetime | None = None


class PlaybookStepCreate(PlaybookStepBase):
    pass


class PlaybookStep(PlaybookStepBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    status: str | None
    time_created: datetime | None = None
    time_updated: datetime | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None
    labels: list["Label"] | None = None
    step_modifiers: list[PlaybookStepModifier] | None = None


PlaybookStep.model_rebuild()
