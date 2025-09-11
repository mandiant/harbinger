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


from enum import Enum
from typing import List

from pydantic import UUID4, BaseModel, ConfigDict


from .label import Label


class FileType(str, Enum):
    empty = ""
    lsass = "lsass_dmp"
    nanodump = "nanodump"

    # Text files
    text = "text"
    secretsdump = "secretsdump"

    # Zip files
    zip = "zip"
    bloodhound_zip = "bloodhound_zip"
    harbinger_zip = "harbinger_zip"
    docx = "docx"

    # Json files
    json = "json"
    bloodhound_json = "bloodhound_json"
    pypykatz_json = "pypykatz_json"
    process_list_json = "process_list_json"
    dir2json_json = "dir2json_json"
    certipy_json = "certipy_json"
    certify_json = "certify_json"

    cast = "cast"

    # Exe / dll / bof
    exe = "exe"
    implant_binary = "implant_binary"
    implant_shellcode = "implant_shellcode"
    bof = "bof"

    # Other data formats
    kdbx = "kdbx"
    xml = "xml"
    dir2json = "dir2json"
    ad_snapshot = "ad_snapshot"
    ccache = "ccache"

    yaml = "yaml"

    # harbinger related files
    harbinger_yaml = "harbinger_yaml"
    terminal_recording = "terminal_recording"


class FileTypes(BaseModel):
    types: List[FileType]


class FileBase(BaseModel):
    filetype: FileType | str | None = None
    magic_mimetype: str | None = ""
    magika_mimetype: str | None = ""
    exiftool: str | None = ""
    md5sum: str | None = ""
    sha1sum: str | None = ""
    sha256sum: str | None = ""


class FileUpdate(FileBase):
    pass


class FileCreate(FileBase):
    filename: str
    bucket: str
    path: str
    internal_task_id: str | None = None
    c2_server_id: str | None = None
    internal_implant_id: str | None = None
    manual_timeline_task_id: str | UUID4 | None = None


class File(FileBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    job_id: UUID4 | None
    filename: str
    bucket: str
    path: str
    processing_status: str | None = ""
    processing_progress: int | None = 0
    processing_note: str | None = ""
    c2_task_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    manual_timeline_task_id: str | UUID4 | None = None

    labels: List["Label"] | None = None
