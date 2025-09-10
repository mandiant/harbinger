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

from pydantic import (UUID4, BaseModel, ConfigDict, field_validator)


from .label import Label


class ShareBase(BaseModel):
    host_id: str | UUID4 | None = None
    name: str | None = ""
    unc_path: str
    type: int | None = None
    remark: str | None = ""

    @field_validator("name", "unc_path", "remark")
    @classmethod
    def clean(cls, v: str) -> str:
        try:
            return v.replace("\x00", "")
        except AttributeError:
            return v

    @field_validator("name", "unc_path")
    @classmethod
    def upper_case(cls, v: str) -> str:
        try:
            return v.upper()
        except AttributeError:
            return v

class ShareCreate(ShareBase):
    pass

class Share(ShareBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime

    labels: List["Label"] | None = None

