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
# Using Enum for validation at the application layer


from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict

from .checklist import ChecklistBase
from .label import Label


class PlanBase(BaseModel):
    name: str
    objective: str | None = None
    status: str | None = ""
    llm_status: str | None = ""


class PlanCreate(PlanBase):
    pass


class PlanUpdate(PlanBase):
    name: str | None = None


class PlanCreated(ChecklistBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class Plan(PlanBase):
    id: UUID4
    time_created: datetime | None = None
    time_updated: datetime | None = None
    # steps: List[PlanStep] = []
    labels: list["Label"] = []
    model_config = ConfigDict(from_attributes=True)


Plan.model_rebuild()
