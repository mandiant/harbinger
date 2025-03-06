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

from pydantic import BaseModel
from harbinger.database import schemas


class FileDownloads(BaseModel):
    id: str
    files: list[schemas.File]
    volume_name: str
    bucket: str = ''


class File(BaseModel):
    id: str
    filename: str
    path: str
    bucket: str


class SocksTask(BaseModel):
    command: str
    arguments: str
    id: str
    proxy: schemas.Proxy | None
    tmate: bool | None
    asciinema: bool | None
    proxychains: bool | None
    env: str | None = ''
    credential: schemas.Credential | None = None
    files: list[schemas.File] | None = []


class SocksTaskResult(BaseModel):
    id: str
    output: list[str] | None = []
    status: schemas.Status
    error: str = ''
    exit_code: int = 0
    files: list[File] | None = []


class Output(BaseModel):
    job_id: str
    output: str


class Files(BaseModel):
    id: str
    files: list[File] = []
