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

from pydantic import (UUID4, BaseModel, ConfigDict)


from .label import Label


class HighlightBase(BaseModel):
    file_id: UUID4 | str | None = None
    c2_task_id: UUID4 | str | None = None
    c2_task_output_id: UUID4 | str | None = None
    proxy_job_output_id: UUID4 | str | None = None
    parse_result_id: UUID4 | str | None = None
    proxy_job_id: UUID4 | str | None = None
    rule_id: int | None = None
    rule_type: str | None = None
    hit: str | None = None
    start: int | None = None
    end: int | None = None
    line: int | None = None

class HighlightCreate(HighlightBase):
    pass

class Highlight(HighlightBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime
    labels: List["Label"] | None = []

