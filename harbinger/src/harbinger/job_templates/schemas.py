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

import json
from typing import Dict, List, Literal, Type

from harbinger.database import crud
from harbinger.job_templates import schemas
from jinja2 import PackageLoader
from jinja2.sandbox import SandboxedEnvironment
from jinja2.ext import do
from pydantic import UUID4, BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from enum import Enum

env = SandboxedEnvironment(
    loader=PackageLoader("harbinger.job_templates", "templates"),
    autoescape=False,
    enable_async=True,
    extensions=[do],
)


class Arguments(BaseModel):
    command: str = ""
    folder: str = ""
    path: str = ""
    sleep: int = 0
    jitter: int = 0
    remotename: str = ""
    host: str = ""
    arguments_str: str = ""
    source: str = ""
    destination: str = ""
    action: str = ""
    port: int = 0
    filename: str = ""
    powershell: str = ""
    tcp: bool = False
    udp: bool = False
    ipv4: bool = False
    ipv6: bool = False
    listening: bool = False
    pid: int = 0
    force: bool = False
    reghive: str = ""
    regkey: str = ""
    recurse: bool = False
    value: str = ""
    data: str = ""
    task_id: str = ""
    url: str = ""


class TemplateList(BaseModel):
    templates: List[str]


class ChainList(BaseModel):
    chains: List[str]


class BaseTemplateModel(BaseModel):
    playbook_id: str | None = None

    class Settings:
        command = ""
        add_labels: list[str] = []

    async def files(self, db: AsyncSession) -> List[str]:
        """Create any objects in the database and minio and return their ids"""
        return []

    async def generate_arguments(self, db: AsyncSession) -> str:
        objects = await self.resolve_objects(db)
        return json.dumps(
            Arguments(**objects, **self.model_dump()).model_dump(exclude_unset=True)
        )

    async def generate_command(self) -> str:
        return self.Settings.command

    async def resolve_objects(self, db: AsyncSession) -> dict[str, str]:
        return {}


class Command(str, Enum):
    ps = "ps"
    ls = "ls"
    download = "download"
    sleep = "sleep"
    rm = "rm"
    upload = "upload"
    runassembly = "runassembly"
    runbof = "runbof"
    cp = "cp"
    cd = "cd"
    mkdir = "mkdir"
    mv = "mv"
    pwd = "pwd"
    runprocess = "runprocess"
    socks = "socks"
    exit = "exit"
    shell = "shell"
    disableetw = "disableetw"
    disableamsi = "disableamsi"
    unhook = "unhook"
    custom = "custom"


class C2ImplantTemplateModel(BaseTemplateModel):
    c2_implant_id: UUID4


class PS(C2ImplantTemplateModel):
    class Settings:
        command = Command.ps


class Shell(C2ImplantTemplateModel):
    command: str

    class Settings:
        command = Command.shell


class LS(C2ImplantTemplateModel):
    folder: str = "."

    class Settings:
        command = Command.ls


class Download(C2ImplantTemplateModel):
    path: str

    class Settings:
        command = Command.download


class Sleep(C2ImplantTemplateModel):
    sleep: int
    jitter: int = 0

    class Settings:
        command = Command.sleep


class RM(C2ImplantTemplateModel):
    path: str

    class Settings:
        command = Command.rm


class Upload(C2ImplantTemplateModel):
    file_id: str
    remotename: str = ""
    path: str = ""
    host: str = ""

    class Settings:
        command = Command.upload

    async def files(self, db: AsyncSession) -> List[str]:
        return [self.file_id]


class ExecuteAssembly(C2ImplantTemplateModel):
    arguments_str: str = ""
    file_id: str = Field(json_schema_extra=dict(filetype="exe"))

    class Settings:
        command = Command.runassembly

    async def files(self, db: AsyncSession) -> List[str]:
        return [self.file_id]


class ExecuteBof(C2ImplantTemplateModel):
    file_id: str = Field(json_schema_extra=dict(filetype="bof"))
    arguments_str: str = ""

    class Settings:
        command = Command.runbof

    async def files(self, db: AsyncSession) -> List[str]:
        return [self.file_id]


class Copy(C2ImplantTemplateModel):
    source: str
    destination: str

    class Settings:
        command = Command.cp


class CD(C2ImplantTemplateModel):
    path: str

    class Settings:
        command = Command.cd


class MkDir(C2ImplantTemplateModel):
    path: str

    class Settings:
        command = Command.mkdir


class MV(C2ImplantTemplateModel):
    source: str
    destination: str

    class Settings:
        command = Command.mv


class PWD(C2ImplantTemplateModel):
    class Settings:
        command = Command.pwd


class RunProcess(C2ImplantTemplateModel):
    command: str = ""

    class Settings:
        command = Command.runprocess


# class Screenshot(C2ImplantTemplateModel):
#     class Settings:
#         command = "screenshot"


class Socks(C2ImplantTemplateModel):
    action: Literal["start", "stop"] = "start"
    port: int = 7001
    task_id: str = ""
    url: str = ""

    class Settings:
        command = Command.socks


class Exit(C2ImplantTemplateModel):
    class Settings:
        command = Command.exit


class DisableEtw(C2ImplantTemplateModel):
    file_id: str = Field(
        json_schema_extra=dict(filetype="bof"),
        default="fce22bd6-48a5-4449-b29e-4069f92113b5",
    )

    class Settings:
        command = Command.disableetw

    async def files(self, db: AsyncSession) -> List[str]:
        return [self.file_id]


class DisableAmsi(C2ImplantTemplateModel):
    file_id: str = Field(json_schema_extra=dict(filetype="bof"), default="")

    class Settings:
        command = Command.disableamsi

    async def files(self, db: AsyncSession) -> List[str]:
        if self.file_id:
            return [self.file_id]
        return []


class Unhook(C2ImplantTemplateModel):
    file_id: str = Field(
        json_schema_extra=dict(filetype="bof"),
        default="663c1e37-77b5-491b-9400-ab36aac88b7d",
    )
    arguments_str: str = "z:ntdll.dll"

    class Settings:
        command = Command.unhook

    async def files(self, db: AsyncSession) -> List[str]:
        return [self.file_id]


class Custom(C2ImplantTemplateModel):
    command: str = ""
    arguments_str: str = ""
    file_id: str = ""

    class Settings:
        command = Command.custom

    async def files(self, db: AsyncSession) -> List[str]:
        return [self.file_id] if self.file_id else []


class MythicParameter(BaseModel):
    name: str
    from_value: str | None = None
    value: str | bool | int | None = None


class MythicTaskMapping(BaseModel):
    command: Command
    agent_command: str | None = None
    parameter: str | None = None
    parameter_format: str | None = None
    parameters: list[MythicParameter] | None = None


class MythicAgent(BaseModel):
    name: str
    icon: str = ""
    task_mapping: list[MythicTaskMapping]


LIST: list[Type[schemas.C2ImplantTemplateModel]] = [
    schemas.PS,
    schemas.Shell,
    schemas.LS,
    # schemas.ListDrives,
    schemas.Download,
    schemas.Sleep,
    schemas.RM,
    schemas.Upload,
    schemas.ExecuteAssembly,
    schemas.ExecuteBof,
    schemas.Copy,
    schemas.CD,
    schemas.MkDir,
    schemas.MV,
    schemas.PWD,
    schemas.RunProcess,
    # schemas.Screenshot,
    schemas.Socks,
    schemas.Exit,
    schemas.DisableAmsi,
    schemas.DisableEtw,
    schemas.Unhook,
    schemas.Custom,
]

C2_JOB_BASE_MAP: Dict[str, Type[schemas.C2ImplantTemplateModel]] = {
    entry.Settings.command: entry for entry in LIST
}
