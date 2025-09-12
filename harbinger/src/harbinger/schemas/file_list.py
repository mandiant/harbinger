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
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, field_validator, model_validator

from .share_file import ShareFileCreate


class BaseParsedShareFile(BaseModel):
    attributes: int = 0
    name: str
    size: int = 0
    timestamp: None | int | datetime = None
    children: list["BaseParsedShareFile"] = []
    type: str = ""
    unc_path: str = ""
    sharename: str = ""
    share_unc_path: str = ""
    depth: int = 0
    hostname: str = ""
    domain: str = ""
    indexed: bool = False
    parents: list["BaseParsedShareFile"] = []

    def count(self) -> int:
        count = len(self.children)
        for child in self.children:
            count += child.count()
        return count

    # Modify the filenames from for example C:\ to \\hostname.domain\C$
    # Raised ValueError if the sharename doesn't start with \\ and the hostname is not defined.
    def parse(self, hostname: str, domain: str, indexer: bool = True):
        self.parents = []
        if not self.name.startswith("\\"):
            if not hostname:
                msg = "Cannot parse the file without hostname"
                raise ValueError(msg)
            host = hostname
            if domain:
                host = f"{host}.{domain}"
            share = self.name.split("\\")[0]
            self.sharename = share.replace(":", "$")
            self.share_unc_path = f"\\\\{host}\\{self.sharename}"
            self.hostname = hostname
            self.domain = domain
            self.name = self.name.replace(share, self.share_unc_path)
        else:
            hostpart = [x for x in self.name.split("\\") if x]
            if "." in hostpart[0]:
                self.hostname, self.domain = hostpart[0].split(".", 1)
            else:
                self.hostname = hostpart[0]
            self.share_unc_path = f"\\\\{ntpath.join(*hostpart[0:2])}"
            self.sharename = hostpart[1]

        split = [n for n in self.name.split("\\") if n][2:]
        parts = split[:-1]

        self.name = ""
        depth = 0

        if split:
            self.name = split[-1]
            self.parents.append(
                BaseParsedShareFile(
                    name="",
                    type="dir",
                    unc_path=self.share_unc_path,
                    indexed=len(parts) == 0 and indexer,
                    depth=0,
                ),
            )
            depth += 1

        for part in parts:
            self.parents.append(
                BaseParsedShareFile(
                    name=part,
                    type="dir",
                    unc_path=ntpath.join(self.share_unc_path, *parts[0:depth]),
                    depth=depth,
                    indexed=False,
                ),
            )
            depth += 1

        self.depth = depth
        self.unc_path = ntpath.join(self.share_unc_path, *split)


class Dir2JsonShareFile(BaseParsedShareFile):
    attributes: int = Field(alias="A", default=0)
    name: str = Field(alias="N")
    size: int = Field(alias="S", default=0)
    timestamp: None | int | datetime = Field(alias="T", default=None)
    children: list["Dir2JsonShareFile"] = Field(alias="C", default=[])

    @field_validator("timestamp")
    @classmethod
    def parse_timestamp(cls, v: int) -> datetime:
        return datetime(1601, 1, 1) + timedelta(microseconds=v / 10)

    @model_validator(mode="after")  # type: ignore
    def set_type(self) -> "Dir2JsonShareFile":
        if not self.type:
            self.type = "dir" if self.attributes & 0x10 else "file"
        return self


class MythicShareFile(BaseParsedShareFile):
    host: str = ""
    is_file: bool = Field(exclude=True)
    access_time: datetime
    creation_time: datetime
    modify_time: datetime
    name: str
    parent_path: str = ""
    children: list["MythicShareFile"] = Field(alias="files", default=[])

    @model_validator(mode="after")  # type: ignore
    def set_type(self) -> "MythicShareFile":
        if not self.type:
            self.type = "file" if self.is_file else "dir"
        return self

    @model_validator(mode="after")  # type: ignore
    def set_name(self) -> "MythicShareFile":
        if self.parent_path:
            self.name = ntpath.join(self.parent_path, self.name)
        return self


class FileList(BaseModel):
    host: str
    parent_path: str
    name: str
    domain: str = ""

    unc_path: str = ""
    sharename: str = ""
    share_unc_path: str = ""
    depth: int = 0

    size: int = 0
    last_accessed: datetime | None = None
    last_modified: datetime | None = None
    files: list["ShareFileCreate"] | None = None

    parents: list["ShareFileCreate"] | None = None

    def to_base_parsed_share_file(self) -> "BaseParsedShareFile":
        result = BaseParsedShareFile(
            name=self.name,
            domain=self.domain,
            unc_path=self.unc_path,
            share_unc_path=self.share_unc_path,
            depth=self.depth,
            size=self.size,
            type="dir",
            indexed=True,
            parents=[],
            children=[],
            sharename=self.sharename,
            hostname=self.host,
        )

        for parent in self.parents or []:
            result.parents.append(
                BaseParsedShareFile(
                    name=parent.name,
                    size=parent.size or 0,
                    type="dir",
                    unc_path=parent.unc_path or "",
                    depth=parent.depth or 0,
                ),
            )

        for file in self.files or []:
            result.children.append(
                BaseParsedShareFile(
                    name=file.name,
                    size=file.size or 0,
                    type=file.type or "",
                    unc_path=file.unc_path or "",
                    depth=file.depth or 0,
                ),
            )
        return result

    # Modify the filenames from for example C:\ to \\hostname.domain\C$
    # Raised ValueError if the sharename doesn't start with \\ and the hostname is not defined.
    def parse(self, indexer: bool = True):
        if not self.name.startswith("\\"):
            # print("not self.name.startswith('\\')")
            if not self.host:
                msg = "Cannot parse the file without hostname"
                raise ValueError(msg)
            share = ""
            if self.parent_path:
                if self.parent_path.startswith("\\"):
                    hostpart = [x for x in self.parent_path.split("\\") if x]
                    if len(hostpart) > 1:
                        share = hostpart[1]
                        self.host = hostpart[0]
                        self.name = ntpath.join(*hostpart[1:], self.name)
                    else:
                        share = self.name
                        self.host = hostpart[0]
                else:
                    share = self.parent_path.split("\\")[0]
                    self.name = f"{self.parent_path}\\{self.name}"
            elif "\\" in self.name:
                share = self.name.split("\\")[0]
            self.sharename = share.replace(":", "$")
            self.share_unc_path = f"\\\\{self.host}\\{self.sharename}"
            self.name = self.name.replace(share, self.share_unc_path)
            if "." in self.host:
                self.host, self.domain = self.host.split(".", 1)
        else:
            hostpart = [x for x in self.name.split("\\") if x]
            if "." in hostpart[0]:
                self.host, self.domain = hostpart[0].split(".", 1)
            else:
                self.host = hostpart[0]
            self.share_unc_path = f"\\\\{ntpath.join(*hostpart[0:2])}"
            self.sharename = hostpart[1]

        split = [n for n in self.name.split("\\") if n][2:]
        parts = split[:-1]

        self.name = ""
        depth = 0
        self.parents = []

        if split:
            self.name = split[-1]
            self.parents.append(
                ShareFileCreate(
                    name="",
                    type="dir",
                    unc_path=self.share_unc_path,
                    indexed=len(parts) == 0 and indexer,
                    depth=0,
                ),
            )
            depth += 1

        for part in parts:
            self.parents.append(
                ShareFileCreate(
                    name=part,
                    type="dir",
                    unc_path=ntpath.join(self.share_unc_path, *parts[0:depth]),
                    depth=depth,
                    indexed=False,
                ),
            )
            depth += 1

        self.depth = depth
        self.unc_path = ntpath.join(self.share_unc_path, *split)
        for file in self.files or []:
            file.fix_fields(self.unc_path, self.depth)
