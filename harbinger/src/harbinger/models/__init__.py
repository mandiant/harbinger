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

# ruff: noqa: F401
# mypy: ignore-errors
from .action import Action
from .action_playbook import ActionPlaybook
from .c2_implant import C2Implant
from .c2_implant_arguments import C2ImplantArguments
from .c2_implant_type import C2ImplantType
from .c2_job import C2Job
from .c2_output import C2Output
from .c2_server import C2Server
from .c2_server_arguments import C2ServerArguments
from .c2_server_status import C2ServerStatus
from .c2_server_type import C2ServerType
from .c2_task import C2Task
from .certificate_authority import CertificateAuthority
from .certificate_authority_map import CertificateAuthorityMap
from .certificate_template import CertificateTemplate
from .certificate_template_permission import CertificateTemplatePermission
from .checklist import Checklist
from .component import Component
from .credential import Credential
from .domain import Domain
from .file import File
from .hash import Hash
from .highlight import Highlight
from .host import Host
from .input_file import InputFile
from .ip_address import IpAddress
from .issue import Issue
from .kerberos import Kerberos
from .label import Label
from .labeled_item import LabeledItem
from .llm_log import LlmLog
from .manual_timeline_task import ManualTimelineTask
from .objectives import Objectives
from .parse_result import ParseResult
from .password import Password
from .plan import Plan
from .plan_step import PlanStep
from .playbook import Playbook
from .playbook_step import PlaybookStep
from .playbook_step_modifier import PlaybookStepModifier
from .playbook_template import PlaybookTemplate
from .process import Process
from .proxy import Proxy
from .proxy_job import ProxyJob
from .proxy_job_output import ProxyJobOutput
from .setting import Setting
from .setting_category import SettingCategory
from .share import Share
from .share_file import ShareFile
from .situational_awareness import SituationalAwareness
from .socks_server import SocksServer
from .suggestion import Suggestion
from .timeline import TimeLine
from .user import User
from ..database.database import Base

try:
    Base.registry.configure()
except AttributeError:
    pass
