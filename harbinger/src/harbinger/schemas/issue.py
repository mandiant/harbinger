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
# --- Graph Schemas ---


from datetime import datetime
from typing import List

from pydantic import (UUID4, BaseModel, ConfigDict)


from .label import Label


class IssueBase(BaseModel):
    name: str | None = None
    description: str | None = None
    impact: str | None = None
    exploitability: str | None = None
    label_id: str | UUID4 | None = None

class IssueCreate(IssueBase):
    pass

class IssueCreated(IssueBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

class Issue(IssueBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    time_created: datetime | None = None
    time_updated: datetime | None = None

    labels: List["Label"] | None = None

