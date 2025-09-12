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

import contextlib
import random
import string
from typing import ClassVar

from fastapi import FastAPI
from fastapi_users.exceptions import InvalidPasswordException
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from harbinger import models
from harbinger.config import get_settings
from harbinger.crud import get_user_db
from harbinger.database import database
from harbinger.database.database import get_async_session
from harbinger.database.users import auth_backend_cookie, get_user_manager

get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


settings = get_settings()


def add_admin(app: FastAPI) -> None:
    auth = AdminAuth("".join(random.choice(string.ascii_lowercase) for _ in range(100)))
    admin = Admin(app, database.engine, base_url="/admin", authentication_backend=auth)
    admin.add_view(UserAdmin)
    admin.add_view(DomainAdmin)
    admin.add_view(PasswordAdmin)
    admin.add_view(KerberosAdmin)
    admin.add_view(CredentialAdmin)
    admin.add_view(ProxyAdmin)
    admin.add_view(ProxyJobAdmin)
    admin.add_view(ProxyJobOutputAdmin)
    admin.add_view(FileAdmin)
    admin.add_view(PlaybookAdmin)
    admin.add_view(PlaybookStepAdmin)
    admin.add_view(C2JobAdmin)
    admin.add_view(HostAdmin)
    admin.add_view(ProcessAdmin)
    admin.add_view(PlaybookTemplateAdmin)
    admin.add_view(LabelAdmin)
    admin.add_view(C2ServerAdmin)
    admin.add_view(C2ServerStatusAdmin)
    admin.add_view(C2ImplantAdmin)
    admin.add_view(C2TaskAdmin)
    admin.add_view(C2OutputAdmin)
    admin.add_view(SituationalAwarenessAdmin)
    admin.add_view(ShareAdmin)
    admin.add_view(ShareFileAdmin)
    admin.add_view(HashAdmin)
    admin.add_view(HighlightAdmin)
    admin.add_view(ParseResultAdmin)
    admin.add_view(ManualTimelineTaskAdmin)
    admin.add_view(SuggestionAdmin)
    admin.add_view(SocksServerAdmin)


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    user = await user_manager.get_by_email(str(username))

                    if user:
                        try:
                            await user_manager.validate_password(
                                str(password),
                                user=user,
                            )

                            strat = auth_backend_cookie.get_strategy()
                            result = await auth_backend_cookie.login(strat, user)  # type: ignore
                            request.session.update(
                                {
                                    "fastapiusersauth": result.headers["set-cookie"].split("=")[1].split(" ")[0][:-1],
                                },
                            )

                            return True
                        except InvalidPasswordException:
                            return False
                    else:
                        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        cookie = request.cookies.get("fastapiusersauth")
        if not cookie:
            cookie = request.session.get("fastapiusersauth")
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    strat = auth_backend_cookie.get_strategy()
                    res = await strat.read_token(cookie, user_manager)  # type: ignore
                    if res:
                        return True
        return False


class UserAdmin(ModelView, model=models.User):
    can_create: ClassVar[bool] = False
    can_edit: ClassVar[bool] = False
    name: ClassVar[str] = "User"
    name_plural: ClassVar[str] = "Users"
    icon: ClassVar[str] = "fa-solid fa-user"
    column_list: ClassVar[list[str]] = ["id", "email", "is_superuser"]
    column_details_list: ClassVar[list[str]] = ["id", "email", "is_active", "is_superuser", "is_verified"]
    column_searchable_list: ClassVar[list[str]] = ["email"]


class DomainAdmin(ModelView, model=models.Domain):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "Domain"
    name_plural: ClassVar[str] = "Domains"
    column_list: ClassVar[list[str]] = ["id", "short_name", "long_name", "time_created"]
    icon: ClassVar[str] = "fa-solid fa-globe"
    column_searchable_list: ClassVar[list[str]] = ["short_name", "long_name"]


class PasswordAdmin(ModelView, model=models.Password):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "Password"
    name_plural: ClassVar[str] = "Passwords"
    column_list: ClassVar[list[str]] = ["id", "password", "nt", "aes256_key", "aes128_key", "time_created"]
    icon: ClassVar[str] = "fa-solid fa-key"
    column_searchable_list: ClassVar[list[str]] = ["password", "nt", "aes256_key", "aes128_key"]


class KerberosAdmin(ModelView, model=models.Kerberos):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "Kerberos"
    name_plural: ClassVar[str] = "Kerberos"
    column_list: ClassVar[list[str]] = [
        "id",
        "client",
        "server",
        "key",
        "auth",
        "start",
        "end",
        "renew",
        "ccache",
        "kirbi",
        "time_created",
    ]
    icon: ClassVar[str] = "fa-solid fa-dog"


class CredentialAdmin(ModelView, model=models.Credential):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "Credential"
    name_plural: ClassVar[str] = "Credentials"
    column_list: ClassVar[list[str]] = [
        "id",
        "domain_id",
        "username",
        "password_id",
        "kerberos_id",
        "note",
        "time_created",
    ]
    icon: ClassVar[str] = "fa-solid fa-fingerprint"
    column_searchable_list: ClassVar[list[str]] = ["username"]


class ProxyAdmin(ModelView, model=models.Proxy):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "Proxy"
    name_plural: ClassVar[str] = "Proxys"
    column_list: ClassVar[list[str]] = [
        "id",
        "host",
        "port",
        "type",
        "status",
        "note",
        "remote_hostname",
        "time_created",
        "username",
        "password",
    ]
    icon: ClassVar[str] = "fa-solid fa-share-nodes"
    column_searchable_list: ClassVar[list[str]] = ["host", "port", "remote_hostname", "username", "password"]


class ProxyJobAdmin(ModelView, model=models.ProxyJob):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "ProxyJob"
    name_plural: ClassVar[str] = "ProxyJobs"
    column_list: ClassVar[list[str]] = [
        "id",
        "credential_id",
        "proxy_id",
        "executor_type",
        "socks_server_id",
        "status",
        "exit_code",
        "command",
        "arguments",
        "# input_files",
        "playbook_id",
        "time_created",
        "time_updated",
        "time_started",
        "time_completed",
    ]
    icon: ClassVar[str] = "fa-solid fa-share-nodes"
    column_searchable_list: ClassVar[list[str]] = ["command", "arguments"]


class ProxyJobOutputAdmin(ModelView, model=models.ProxyJobOutput):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "ProxyJobOutput"
    name_plural: ClassVar[str] = "ProxyJobOutputs"
    column_list: ClassVar[list[str]] = ["id", "job_id", "output", "created_at", "output_type"]
    icon: ClassVar[str] = "fa-solid fa-server"
    column_searchable_list: ClassVar[list[str]] = ["output"]


class FileAdmin(ModelView, model=models.File):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "File"
    name_plural: ClassVar[str] = "Files"
    column_list: ClassVar[list[str]] = [
        "id",
        "job_id",
        "filename",
        "bucket",
        "path",
        "filetype",
        "status",
        "processing_status",
        "processing_progress",
        "processing_note",
        "c2_implant_id",
        "c2_task_id",
        "time_created",
    ]
    icon: ClassVar[str] = "fa-solid fa-file"
    column_searchable_list: ClassVar[list[str]] = ["filename", "bucket", "path", "filetype"]


class PlaybookAdmin(ModelView, model=models.Playbook):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "Playbook"
    name_plural: ClassVar[str] = "Playbooks"
    column_list: ClassVar[list[str]] = [
        "id",
        "playbook_name",
        "description",
        "status",
        "arguments",
        "steps",
        "completed",
        "suggestion_id",
        "time_created",
        "time_updated",
        "time_started",
        "time_completed",
    ]
    icon: ClassVar[str] = "fa-solid fa-play"
    column_searchable_list: ClassVar[list[str]] = ["playbook_name", "description", "status", "arguments"]


class PlaybookStepAdmin(ModelView, model=models.PlaybookStep):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "PlaybookStep"
    name_plural: ClassVar[str] = "PlaybookSteps"
    column_list: ClassVar[list[str]] = [
        "id",
        "number",
        "label",
        "depends_on",
        "playbook_id",
        "proxy_job_id",
        "c2_job_id",
        "status",
        "delay",
        "execute_after",
        "time_created",
        "time_updated",
        "time_started",
        "time_completed",
    ]
    column_searchable_list: ClassVar[list[str]] = ["label", "status"]


class C2JobAdmin(ModelView, model=models.C2Job):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "C2Job"
    name_plural: ClassVar[str] = "C2Jobs"
    column_list: ClassVar[list[str]] = [
        "id",
        "status",
        "c2_type",
        "c2_task_id",
        "c2_server_id",
        "c2_implant_id",
        "internal_id",
        "command",
        "arguments",
        "playbook_id",
        "message",
        "time_created",
        "time_updated",
        "time_started",
        "time_completed",
        "add_labels",
    ]
    column_searchable_list: ClassVar[list[str]] = ["command", "arguments"]


class HostAdmin(ModelView, model=models.Host):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "Host"
    name_plural: ClassVar[str] = "Hosts"
    column_list: ClassVar[list[str]] = [
        "id",
        "domain_id",
        "name",
        "objectid",
        "owned",
        "domain",
        "fqdn",
        "time_created",
    ]
    icon: ClassVar[str] = "fa-solid fa-server"
    column_searchable_list: ClassVar[list[str]] = ["name"]


class ProcessAdmin(ModelView, model=models.Process):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "Process"
    name_plural: ClassVar[str] = "Process"
    column_list: ClassVar[list[str]] = [
        "id",
        "process_id",
        "architecture",
        "name",
        "user",
        "bin_path",
        "parent_process_id",
        "command_line",
        "description",
        "handle",
        "host_id",
        "number",
        "c2_implant_id",
    ]
    icon: ClassVar[str] = "fa-solid fa-microchip"
    column_searchable_list: ClassVar[list[str]] = ["name"]


class PlaybookTemplateAdmin(ModelView, model=models.PlaybookTemplate):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "PlaybookTemplate"
    name_plural: ClassVar[str] = "PlaybookTemplates"
    column_list: ClassVar[list[str]] = ["id", "name", "icon", "tactic", "technique", "step_delay", "yaml"]
    column_searchable_list: ClassVar[list[str]] = ["name", "description"]


class LabelAdmin(ModelView, model=models.Label):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "Label"
    name_plural: ClassVar[str] = "Labels"
    column_list: ClassVar[list[str]] = ["id", "name", "category", "color", "time_created"]
    icon: ClassVar[str] = "fa-solid fa-tag"
    column_searchable_list: ClassVar[list[str]] = ["name", "category"]


class C2ServerAdmin(ModelView, model=models.C2Server):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "C2Server"
    name_plural: ClassVar[str] = "C2Servers"
    column_list: ClassVar[list[str]] = [
        "id",
        "type",
        "time_created",
        "name",
        "hostname",
        "username",
        "password",
        "port",
        "ca_certificate",
        "certificate",
        "private_key",
        "token",
    ]
    icon: ClassVar[str] = "fa-solid fa-server"
    column_searchable_list: ClassVar[list[str]] = ["name", "hostname", "username", "password", "port"]


class C2ServerStatusAdmin(ModelView, model=models.C2ServerStatus):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "C2ServerStatus"
    name_plural: ClassVar[str] = "C2ServerStatus"
    column_list: ClassVar[list[str]] = ["id", "c2_server_id", "name", "status", "message"]
    icon: ClassVar[str] = "fa-solid fa-satellite-dish"


class C2ImplantAdmin(ModelView, model=models.C2Implant):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "C2Implant"
    name_plural: ClassVar[str] = "C2Implants"
    column_list: ClassVar[list[str]] = [
        "id",
        "time_created",
        "c2_server_id",
        "internal_id",
        "c2_type",
        "payload_type",
        "name",
        "hostname",
        "description",
        "sleep",
        "jitter",
        "os",
        "pid",
        "architecture",
        "process",
        "username",
        "ip",
        "external_ip",
        "domain",
        "last_checkin",
        "raw_json",
        "host_id",
    ]
    icon: ClassVar[str] = "fa-solid fa-virus"
    column_searchable_list: ClassVar[list[str]] = [
        "name",
        "hostname",
        "description",
        "pid",
        "ip",
        "external_ip",
    ]


class C2TaskAdmin(ModelView, model=models.C2Task):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "C2Task"
    name_plural: ClassVar[str] = "C2Tasks"
    column_list: ClassVar[list[str]] = [
        "id",
        "time_created",
        "internal_id",
        "c2_implant_id",
        "c2_server_id",
        "status",
        "original_params",
        "display_params",
        "time_started",
        "time_completed",
        "command_name",
        "operator",
        "raw_json",
    ]
    column_searchable_list: ClassVar[list[str]] = ["command_name", "display_params", "original_params"]


class C2OutputAdmin(ModelView, model=models.C2Output):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "C2Output"
    name_plural: ClassVar[str] = "C2Outputs"
    column_list: ClassVar[list[str]] = [
        "id",
        "time_created",
        "c2_implant_id",
        "c2_task_id",
        "c2_server_id",
        "internal_id",
        "timestamp",
        "response_text",
        "response_bytes",
        "output_type",
        "raw_json",
    ]
    column_searchable_list: ClassVar[list[str]] = ["response_text"]


class SituationalAwarenessAdmin(ModelView, model=models.SituationalAwareness):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "SituationalAwareness"
    name_plural: ClassVar[str] = "SituationalAwareness"
    column_list: ClassVar[list[str]] = [
        "id",
        "time_created",
        "name",
        "category",
        "value_string",
        "value_int",
        "value_bool",
        "value_json",
        "domain_id",
    ]
    icon: ClassVar[str] = "fa-solid fa-globe"
    column_searchable_list: ClassVar[list[str]] = ["name", "value_string", "value_int"]


class ShareAdmin(ModelView, model=models.Share):
    can_create: ClassVar[bool] = True
    name: ClassVar[str] = "Share"
    name_plural: ClassVar[str] = "Shares"
    column_list: ClassVar[list[str]] = [
        "id",
        "time_created",
        "host_id",
        "name",
        "unc_path",
        "type",
        "remark",
    ]
    icon: ClassVar[str] = "fa-solid fa-square-share-nodes"
    column_searchable_list: ClassVar[list[str]] = ["name", "unc_path"]


class ShareFileAdmin(ModelView, model=models.ShareFile):
    can_create: ClassVar[bool] = True
    name: ClassVar[str] = "ShareFile"
    name_plural: ClassVar[str] = "ShareFiles"
    column_list: ClassVar[list[str]] = [
        "id",
        "time_created",
        "type",
        "file_id",
        "parent_id",
        "share_id",
        "size",
        "last_accessed",
        "last_modified",
        "created",
        "unc_path",
        "depth",
        "name",
        "downloaded",
        "indexed",
    ]
    icon: ClassVar[str] = "fa-solid fa-file"
    column_searchable_list: ClassVar[list[str]] = ["name", "unc_path"]


class HashAdmin(ModelView, model=models.Hash):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "Hash"
    name_plural: ClassVar[str] = "Hashes"
    column_list: ClassVar[list[str]] = ["id", "time_created", "hash", "type", "hashcat_id", "status"]
    icon: ClassVar[str] = "fa-solid fa-hashtag"
    column_searchable_list: ClassVar[list[str]] = ["hash", "type"]


class HighlightAdmin(ModelView, model=models.Highlight):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "Highlight"
    name_plural: ClassVar[str] = "Highlights"
    column_list: ClassVar[list[str]] = [
        "id",
        "time_created",
        "file_id",
        "c2_task_id",
        "c2_task_output_id",
        "proxy_job_output_id",
        "proxy_job_id",
        "parse_result_id",
        "rule_id",
        "rule_type",
        "hit",
        "start",
        "end",
        "line",
    ]
    icon: ClassVar[str] = "fa-solid fa-server"


class ParseResultAdmin(ModelView, model=models.ParseResult):
    can_create: ClassVar[bool] = False
    name: ClassVar[str] = "ParseResult"
    name_plural: ClassVar[str] = "ParseResults"
    column_list: ClassVar[list[str]] = [
        "id",
        "time_created",
        "file_id",
        "parser",
        "log",
        "c2_task_id",
        "c2_task_output_id",
        "proxy_job_output_id",
        "proxy_job_id",
    ]
    icon: ClassVar[str] = "fa-solid fa-server"


class ManualTimelineTaskAdmin(ModelView, model=models.ManualTimelineTask):
    can_create: ClassVar[bool] = True
    name: ClassVar[str] = "ManualTimelineTask"
    name_plural: ClassVar[str] = "ManualTimelineTasks"
    column_list: ClassVar[list[str]] = [
        "id",
        "time_created",
        "status",
        "arguments",
        "time_started",
        "time_completed",
        "command_name",
        "operator",
        "output",
        "hostname",
    ]
    icon: ClassVar[str] = "fa-solid fa-server"


class SuggestionAdmin(ModelView, model=models.Suggestion):
    can_create: ClassVar[bool] = True
    name: ClassVar[str] = "Suggestion"
    name_plural: ClassVar[str] = "Suggestions"
    column_list: ClassVar[list[str]] = [
        "id",
        "name",
        "reason",
        "arguments",
        "playbook_template_id",
        "time_created",
        "time_updated",
    ]
    icon: ClassVar[str] = "fa-solid fa-server"


class SocksServerAdmin(ModelView, model=models.SocksServer):
    can_create: ClassVar[bool] = True
    name: ClassVar[str] = "SocksServer"
    name_plural: ClassVar[str] = "SocksServers"
    column_list: ClassVar[list[str]] = [
        "id",
        "type",
        "hostname",
        "operating_system",
        "status",
        "time_created",
    ]
    icon: ClassVar[str] = "fa-solid fa-server"
