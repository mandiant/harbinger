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
from fastapi import FastAPI
from harbinger.database import database
from harbinger import models
from harbinger.database.users import get_user_manager, auth_backend_cookie

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from harbinger.config import get_settings
from harbinger.database.database import get_async_session
from harbinger.crud import get_user_db
from fastapi_users.exceptions import InvalidPasswordException

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
                            await user_manager.validate_password(str(password), user=user)

                            strat = auth_backend_cookie.get_strategy()
                            result = await auth_backend_cookie.login(strat, user)  # type: ignore
                            request.session.update({"fastapiusersauth": result.headers['set-cookie'].split('=')[1].split(' ')[0][:-1]})

                            return True
                        except InvalidPasswordException:
                            return False
                    else:
                        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        cookie = request.cookies.get('fastapiusersauth')
        if not cookie:
            cookie = request.session.get('fastapiusersauth')
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    strat = auth_backend_cookie.get_strategy()
                    res = await strat.read_token(cookie, user_manager)  # type: ignore
                    if res:
                        return True
        return False


class UserAdmin(ModelView, model=models.User):
    can_create = False
    can_edit = False
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    column_list = ['id', 'email', 'is_superuser']
    column_details_list = ['id', 'email', 'is_active', 'is_superuser', 'is_verified']
    column_searchable_list = ['email']


class DomainAdmin(ModelView, model=models.Domain):
    can_create = False
    name = "Domain"
    name_plural = "Domains"
    column_list = ['id', 'short_name', 'long_name', 'time_created']
    icon = "fa-solid fa-globe"
    column_searchable_list = ['short_name', 'long_name']


class PasswordAdmin(ModelView, model=models.Password):
    can_create = False
    name = "Password"
    name_plural = "Passwords"
    column_list = ['id', 'password', 'nt', 'aes256_key', 'aes128_key', 'time_created']
    icon = "fa-solid fa-key"
    column_searchable_list = ['password', 'nt', 'aes256_key', 'aes128_key']


class KerberosAdmin(ModelView, model=models.Kerberos):
    can_create = False
    name = "Kerberos"
    name_plural = "Kerberos"
    column_list = ['id', 'client', 'server', 'key', 'auth', 'start', 'end', 'renew', 'ccache', 'kirbi', 'time_created']
    icon = "fa-solid fa-dog"


class CredentialAdmin(ModelView, model=models.Credential):
    can_create = False
    name = "Credential"
    name_plural = "Credentials"
    column_list = ['id', 'domain_id', 'username', 'password_id', 'kerberos_id', 'note', 'time_created']
    icon = "fa-solid fa-fingerprint"
    column_searchable_list = ['username']


class ProxyAdmin(ModelView, model=models.Proxy):
    can_create = False
    name = "Proxy"
    name_plural = "Proxys"
    column_list = ['id', 'host', 'port', 'type', 'status', 'note', 'remote_hostname', 'time_created', 'username', 'password']
    icon = "fa-solid fa-share-nodes"
    column_searchable_list = ['host', 'port', 'remote_hostname', 'username', 'password']


class ProxyJobAdmin(ModelView, model=models.ProxyJob):
    can_create = False
    name = "ProxyJob"
    name_plural = "ProxyJobs"
    column_list = ['id', 'credential_id', 'proxy_id', 'executor_type', 'socks_server_id', 'status', 'exit_code', 'command', 'arguments', '# input_files', 'playbook_id', 'time_created', 'time_updated', 'time_started', 'time_completed']
    icon = "fa-solid fa-share-nodes"
    column_searchable_list = ['command', 'arguments']


class ProxyJobOutputAdmin(ModelView, model=models.ProxyJobOutput):
    can_create = False
    name = "ProxyJobOutput"
    name_plural = "ProxyJobOutputs"
    column_list = ['id', 'job_id', 'output', 'created_at', 'output_type']
    icon = "fa-solid fa-server"
    column_searchable_list = ['output']


class FileAdmin(ModelView, model=models.File):
    can_create = False
    name = "File"
    name_plural = "Files"
    column_list = ['id', 'job_id', 'filename', 'bucket', 'path', 'filetype', 'status', 'processing_status', 'processing_progress', 'processing_note', 'c2_implant_id', 'c2_task_id', 'time_created']
    icon = "fa-solid fa-file"
    column_searchable_list = ['filename', 'bucket', 'path', 'filetype']


class PlaybookAdmin(ModelView, model=models.Playbook):
    can_create = False
    name = "Playbook"
    name_plural = "Playbooks"
    column_list = ['id', 'playbook_name', 'description', 'status', 'arguments', 'steps', 'completed', 'suggestion_id', 'time_created', 'time_updated', 'time_started', 'time_completed']
    icon = "fa-solid fa-play"
    column_searchable_list = ['playbook_name', 'description', 'status', 'arguments']


class PlaybookStepAdmin(ModelView, model=models.PlaybookStep):
    can_create = False
    name = "PlaybookStep"
    name_plural = "PlaybookSteps"
    column_list = ['id', 'number', 'label', 'depends_on', 'playbook_id', 'proxy_job_id', 'c2_job_id', 'status', 'delay', 'execute_after', 'time_created', 'time_updated', 'time_started', 'time_completed']
    column_searchable_list = ['label', 'status']


class C2JobAdmin(ModelView, model=models.C2Job):
    can_create = False
    name = "C2Job"
    name_plural = "C2Jobs"
    column_list = ['id', 'status', 'c2_type', 'c2_task_id', 'c2_server_id', 'c2_implant_id', 'internal_id', 'command', 'arguments', 'playbook_id', 'message', 'time_created', 'time_updated', 'time_started', 'time_completed', 'add_labels']
    column_searchable_list = ['command', 'arguments']


class HostAdmin(ModelView, model=models.Host):
    can_create = False
    name = "Host"
    name_plural = "Hosts"
    column_list = ['id', 'domain_id', 'name', 'objectid', 'owned', 'domain', 'fqdn', 'time_created']
    icon = "fa-solid fa-server"
    column_searchable_list = ['name']


class ProcessAdmin(ModelView, model=models.Process):
    can_create = False
    name = "Process"
    name_plural = "Process"
    column_list = ['id', 'process_id', 'architecture', 'name', 'user', 'bin_path', 'parent_process_id', 'command_line', 'description', 'handle', 'host_id', 'number', 'c2_implant_id']
    icon = "fa-solid fa-microchip"
    column_searchable_list = ['name']


class PlaybookTemplateAdmin(ModelView, model=models.PlaybookTemplate):
    can_create = False
    name = "PlaybookTemplate"
    name_plural = "PlaybookTemplates"
    column_list = ['id', 'name', 'icon', 'tactic', 'technique', 'step_delay', 'yaml']
    column_searchable_list = ['name', 'description']


class LabelAdmin(ModelView, model=models.Label):
    can_create = False
    name = "Label"
    name_plural = "Labels"
    column_list = ['id', 'name', 'category', 'color', 'time_created']
    icon = "fa-solid fa-tag"
    column_searchable_list = ['name', 'category']


class C2ServerAdmin(ModelView, model=models.C2Server):
    can_create = False
    name = "C2Server"
    name_plural = "C2Servers"
    column_list = ['id', 'type', 'time_created', 'name', 'hostname', 'username', 'password', 'port', 'ca_certificate', 'certificate', 'private_key', 'token']
    icon = "fa-solid fa-server"
    column_searchable_list = ['name', 'hostname', 'username', 'password', 'port']


class C2ServerStatusAdmin(ModelView, model=models.C2ServerStatus):
    can_create = False
    name = "C2ServerStatus"
    name_plural = "C2ServerStatus"
    column_list = ['id', 'c2_server_id', 'name', 'status', 'message']
    icon = "fa-solid fa-satellite-dish"


class C2ImplantAdmin(ModelView, model=models.C2Implant):
    can_create = False
    name = "C2Implant"
    name_plural = "C2Implants"
    column_list = ['id', 'time_created', 'c2_server_id', 'internal_id', 'c2_type', 'payload_type', 'name', 'hostname', 'description', 'sleep', 'jitter', 'os', 'pid', 'architecture', 'process', 'username', 'ip', 'external_ip', 'domain', 'last_checkin', 'raw_json', 'host_id']
    icon = "fa-solid fa-virus"
    column_searchable_list = ['name', 'hostname', 'description', 'pid', 'ip', 'external_ip']


class C2TaskAdmin(ModelView, model=models.C2Task):
    can_create = False
    name = "C2Task"
    name_plural = "C2Tasks"
    column_list = ['id', 'time_created', 'internal_id', 'c2_implant_id', 'c2_server_id', 'status', 'original_params', 'display_params', 'time_started', 'time_completed', 'command_name', 'operator', 'raw_json']
    column_searchable_list = ['command_name', 'display_params', 'original_params']


class C2OutputAdmin(ModelView, model=models.C2Output):
    can_create = False
    name = "C2Output"
    name_plural = "C2Outputs"
    column_list = ['id', 'time_created', 'c2_implant_id', 'c2_task_id', 'c2_server_id', 'internal_id', 'timestamp', 'response_text', 'response_bytes', 'output_type', 'raw_json']
    column_searchable_list = ['response_text']


class SituationalAwarenessAdmin(ModelView, model=models.SituationalAwareness):
    can_create = False
    name = "SituationalAwareness"
    name_plural = "SituationalAwareness"
    column_list = ['id', 'time_created', 'name', 'category', 'value_string', 'value_int', 'value_bool', 'value_json', 'domain_id']
    icon = "fa-solid fa-globe"
    column_searchable_list = ['name', 'value_string', 'value_int']


class ShareAdmin(ModelView, model=models.Share):
    can_create = True
    name = "Share"
    name_plural = "Shares"
    column_list = ['id', 'time_created', 'host_id', 'name', 'unc_path', 'type', 'remark']
    icon = "fa-solid fa-square-share-nodes"
    column_searchable_list = ['name', 'unc_path']


class ShareFileAdmin(ModelView, model=models.ShareFile):
    can_create = True
    name = "ShareFile"
    name_plural = "ShareFiles"
    column_list = ['id', 'time_created', 'type', 'file_id', 'parent_id', 'share_id', 'size', 'last_accessed', 'last_modified', 'created', 'unc_path', 'depth', 'name', 'downloaded', 'indexed']
    icon = "fa-solid fa-file"
    column_searchable_list = ['name', 'unc_path']


class HashAdmin(ModelView, model=models.Hash):
    can_create = False
    name = "Hash"
    name_plural = "Hashes"
    column_list = ['id', 'time_created', 'hash', 'type', 'hashcat_id', 'status']
    icon = "fa-solid fa-hashtag"
    column_searchable_list = ['hash', 'type']


class HighlightAdmin(ModelView, model=models.Highlight):
    can_create = False
    name = "Highlight"
    name_plural = "Highlights"
    column_list = ['id', 'time_created', 'file_id', 'c2_task_id', 'c2_task_output_id', 'proxy_job_output_id', 'proxy_job_id', 'parse_result_id', 'rule_id', 'rule_type', 'hit', 'start', 'end', 'line']
    icon = "fa-solid fa-server"


class ParseResultAdmin(ModelView, model=models.ParseResult):
    can_create = False
    name = "ParseResult"
    name_plural = "ParseResults"
    column_list = ['id', 'time_created', 'file_id', 'parser', 'log', 'c2_task_id', 'c2_task_output_id', 'proxy_job_output_id', 'proxy_job_id']
    icon = "fa-solid fa-server"


class ManualTimelineTaskAdmin(ModelView, model=models.ManualTimelineTask):
    can_create = True
    name = "ManualTimelineTask"
    name_plural = "ManualTimelineTasks"
    column_list = ['id', 'time_created', 'status', 'arguments', 'time_started', 'time_completed', 'command_name', 'operator', 'output', 'hostname']
    icon = "fa-solid fa-server"


class SuggestionAdmin(ModelView, model=models.Suggestion):
    can_create = True
    name = "Suggestion"
    name_plural = "Suggestions"
    column_list = ['id', 'name', 'reason', 'arguments', 'playbook_template_id', 'time_created', 'time_updated']
    icon = "fa-solid fa-server"


class SocksServerAdmin(ModelView, model=models.SocksServer):
    can_create = True
    name = "SocksServer"
    name_plural = "SocksServers"
    column_list = ['id', 'type', 'hostname', 'operating_system', 'status', 'time_created']
    icon = "fa-solid fa-server"
