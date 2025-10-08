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

from pydantic import UUID4, BaseModel, ConfigDict

from .label import Label
from .suggestion import SuggestionBaseRequest


class PlaybookPreview(BaseModel):
    steps: str
    valid: bool
    errors: str = ""
    steps_errors: str | None = ""


class PlaybookDetectionRiskSuggestion(SuggestionBaseRequest):
    additional_prompt: str = ""
    playbook_id: str


class PlaybookBase(BaseModel):
    playbook_name: str | None = None
    description: str | None = None
    playbook_template_id: str | UUID4 | None = None


class PlaybookCreate(PlaybookBase):
    pass


class Playbook(PlaybookBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    status: str | None = None
    steps: int | None = None
    completed: int | None = None
    arguments: dict | None = None
    time_created: datetime | None = None
    time_updated: datetime | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None
    suggestion_id: UUID4 | None = None

    labels: list["Label"] | None = None


class PlaybookGraph(Playbook):
    graph: str = ""
    correct: bool = True
