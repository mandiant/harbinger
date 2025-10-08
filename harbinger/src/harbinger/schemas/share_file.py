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


import ntpath
from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict, model_validator

from .label import Label


class ShareFileBase(BaseModel):
    type: str | None = ""
    file_id: str | UUID4 | None = None
    parent_id: str | UUID4 | None = None
    share_id: str | UUID4 | None = None
    size: int | None = None
    last_accessed: datetime | None = None
    last_modified: datetime | None = None
    created: datetime | None = None
    unc_path: str | None = None
    depth: int | None = None
    extension: str | None = None
    name: str
    downloaded: bool = False
    indexed: bool = False


class ShareFileCreate(ShareFileBase):
    @model_validator(mode="after")  # type: ignore
    def set_extension(self) -> "ShareFileCreate":
        if "." in self.name:
            self.extension = self.name.split(".")[-1].lower()
        return self

    def fix_fields(self, parent_unc_path: str, depth: int) -> None:
        if not self.unc_path:
            self.unc_path = ntpath.join(parent_unc_path, self.name)
        if not self.depth:
            self.depth = depth


class ShareFileUpdate(ShareFileBase):
    name: str | None = None
    type: str | None = None


class ShareFile(ShareFileBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime

    labels: list["Label"] | None = None


ShareFile.model_rebuild()
