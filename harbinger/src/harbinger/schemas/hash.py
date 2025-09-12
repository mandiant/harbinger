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
from typing import TYPE_CHECKING

from pydantic import UUID4, BaseModel, field_validator

if TYPE_CHECKING:
    from .label import Label


class HashBase(BaseModel):
    hash: str
    type: str
    hashcat_id: int = 0

    @field_validator("hash")
    @classmethod
    def remove_nullbytes(cls, v: str) -> str:
        return v.replace("\x00", "")


class HashCreate(HashBase):
    pass


class Hash(HashBase):
    id: UUID4
    time_created: datetime
    status: str | None = ""
    labels: list["Label"] | None = []
