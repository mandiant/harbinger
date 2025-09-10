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

import os
from typing import List

from harbinger.config import get_settings
from harbinger.job_templates.proxy.base import JobTemplateModel
from harbinger.job_templates.schemas import env
from pydantic import Field, field_validator, ValidationInfo
from harbinger import crud
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from harbinger.files.client import upload_file

settings = get_settings()


class TestTemplate(JobTemplateModel):
    message: str = "test"

    class Settings:
        command = "echo"
        template_str = "{{ message }}"


class Sleep(JobTemplateModel):
    duration: int = 20

    class Settings:
        command = "sleep"
        template_str = "{{ duration }}"


class UploadFile(JobTemplateModel):
    """Upload a file over smb."""

    file_id: str
    credential_id: str
    target_computer: str
    share: str = "C$"
    path: str = "Windows/temp"

    async def files(self, db: AsyncSession) -> List[str]:
        template = env.get_template("upload_file.jinja2")
        objects = await self.resolve_objects(db)
        result = await template.render_async(**self.model_dump(), **objects)

        file_db = await crud.add_file(
            db,
            filename="commands.txt",
            bucket=settings.minio_default_bucket,
            path="",
            filetype="text",
        )
        file_id = str(file_db.id)

        path = os.path.join("harbinger", f"{file_id}_commands.txt")

        await upload_file(path, result.encode("utf-8"))

        await crud.update_file_path(db, file_id=file_id, path=path)
        return [self.file_id, file_id]

    class Settings:
        command = "smbclient.py"
        template = "smbclient_upload.jinja2"

    async def resolve_objects(self, db: AsyncSession) -> dict:
        cred = await crud.get_credential(credential_id=self.credential_id)
        file = await crud.get_file(self.file_id)
        return dict(credential=cred, file=file)


class CredJobTemplateModel(JobTemplateModel):
    extra_args: str | None = None
    credential_id: str

    async def resolve_objects(self, db: AsyncSession) -> dict:
        cred = await crud.get_credential(credential_id=self.credential_id)
        return dict(credential=cred)


class DownloadFile(CredJobTemplateModel):
    target_computer: str
    share: str = "C$"
    path: str | None = None
    filename: str

    class Settings:
        command = "smbclient.py"
        template = "smbclient.py.jinja2"

    async def files(self, db: AsyncSession) -> List[str]:
        template = env.get_template("download_file.jinja2")
        objects = await self.resolve_objects(db)
        result = await template.render_async(**self.dict(), **objects)
        file_db = await crud.add_file(
            db,
            filename="commands.txt",
            bucket=settings.minio_default_bucket,
            path="",
            filetype="text",
        )
        file_id = str(file_db.id)
        path = os.path.join("harbinger", f"{file_id}_commands.txt")
        await upload_file(path, result.encode("utf-8"))
        await crud.update_file_path(db, file_id=file_id, path=path)
        return [file_id]


class SecretsDump(CredJobTemplateModel):
    """Run secretsdump against a target."""

    target_computer: str

    class Settings:
        command = "secretsdump.py"
        template = "secretsdump.py.jinja2"


class SMBClient(CredJobTemplateModel):
    """Run smbclient against a target."""

    target_computer: str

    class Settings:
        command = "smbclient.py"
        template = "smbclient.py.jinja2"


class CertipyFind(CredJobTemplateModel):
    class Settings:
        command = "certipy"
        template = "certipy_find.jinja2"


class WmiExec(CredJobTemplateModel):
    exec_path: str
    target_computer: str
    no_output: bool = True

    class Settings:
        command = "wmiexec.py"
        template = "wmiexec.py.jinja2"


class AtExec(CredJobTemplateModel):
    exec_path: str
    target_computer: str
    no_output: bool = True

    class Settings:
        command = "atexec.py"
        template = "wmiexec.py.jinja2"


class BloodHoundPython(CredJobTemplateModel):
    dc_only: bool = True
    target_computer: str | None = Field(title="Optional dc to use")

    class Settings:
        command = "bloodhound-python"
        template = "bloodhound-python.jinja2"


# class SharpHound(CredJobTemplateModel):
#     dc_only: bool = True
#     executor_type: schemas.ExecutorTypeName = schemas.ExecutorTypeName.windows

#     class Settings:
#         command = "SharpHound.exe"
#         template = "sharphound.jinja2"


# class Snuffles(SharpHound):
#     class Settings:
#         command = "Snuffles.exe"
#         template = "sharphound.jinja2"


class WhiskerActionEnum(str, Enum):
    """Whisker action to execute"""

    list = "list"
    add = "add"
    remove = "remove"
    clear = "clear"
    info = "info"
    export = "export"


class PyWhisker(CredJobTemplateModel):
    target_user: str
    action: WhiskerActionEnum

    class Settings:
        command = "pywhisker.py"
        template = "pywhisker.jinja2"


class ListProcesses(CredJobTemplateModel):
    target_computer: str | None = Field(title="Computer to list processes")
    load_owners: bool = Field(
        title="Retrieve the owners of the processes?", default=False
    )

    class Settings:
        command = "list_processes.py"
        template = "list_processes.jinja2"


class Custom(JobTemplateModel):
    command: str
    arguments: str
    input_files: list[str] | None = None

    class Settings:
        command_str = "{{ command }}"
        template_str = "{{ arguments }}"

    async def files(self, db: AsyncSession) -> List[str]:
        result = []
        for file in self.input_files or []:
            if await crud.get_file(file):
                result.append(file)
        return result

    @field_validator('arguments')
    @classmethod
    def remove_newlines_from_arguments(cls, v: str, info: ValidationInfo) -> str:
        """Removes newline characters from the arguments string."""
        return v.replace('\n', ' ').replace('\r', '')
