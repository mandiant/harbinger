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


from pydantic import UUID4, BaseModel, ConfigDict

from .label import Label


class ChecklistBase(BaseModel):
    domain_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    phase: str | None = None
    name: str | None = None
    status: str | None = None


class ChecklistCreate(ChecklistBase):
    pass


class ChecklistCreated(ChecklistBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class Checklist(ChecklistBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

    labels: list["Label"] | None = None


Checklist.model_rebuild()
