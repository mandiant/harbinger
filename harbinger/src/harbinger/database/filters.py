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

from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger.database import models
from pydantic import UUID4


class LabelFilter(Filter):
    id__in: list[str] | None = None
    name__in: list[str] | None = None
    category: str | None = None
    name__not_in: list[str] | None = None

    class Constants(Filter.Constants):
        model = models.Label


class FileFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    filetype: str | None = None
    job_id: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.File
        search_model_fields = ["filename", "path", "filetype", "magic_mimetype", "magika_mimetype"]


class HostFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    hostname: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Host
        search_model_fields = ["name", "objectid", "fqdn"]


class ShareFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))
    host_id: str | None = None

    class Constants(Filter.Constants):
        model = models.Share
        search_model_fields = ["name", "unc_path", "remark"]


class ImplantFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))
    c2_server_id: UUID4 | None = None
    host_id: UUID4 | None = None
    hostname: str | None = None
    os: str | None = None
    payload_type: str | None = None
    c2_type: str | None = None
    username: str | None = None
    domain: str | None = None

    class Constants(Filter.Constants):
        model = models.C2Implant
        search_model_fields = ["name", "hostname", "description", "username", "domain"]


class PlaybookTemplateFilter(Filter):
    order_by: list[str] | None = ["name"]
    search: str | None = None
    tactic: str | None = None
    technique: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.PlaybookTemplate
        search_model_fields = ["name", "yaml", "tactic", "technique"]


class C2TaskFilter(Filter):
    order_by: list[str] | None = ["-time_completed"]
    search: str | None = None
    c2_implant_id: str | UUID4 | None = None 
    status: str | None = None
    command_name: str | None = None
    operator: str | None = None
    processing_status: str | None = None
    internal_id: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.C2Task
        search_model_fields = ["original_params", "display_params", "command_name"]


class C2OutputFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    c2_implant_id: UUID4 | None = None 
    c2_server_id: UUID4 | None = None 
    c2_task_id: UUID4 | None = None 
    output_type: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.C2Output
        search_model_fields = ["response_text"]


class SocksServerFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    operating_system: str | None = None
    type: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))
    status: str | None = None

    class Constants(Filter.Constants):
        model = models.SocksServer
        search_model_fields = ["type", "hostname", "operating_system"]


class SocksJobFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    command: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))
    status: str | None = None
    processing_status: str | None = None

    class Constants(Filter.Constants):
        model = models.ProxyJob
        search_model_fields = ["command", "arguments"]


class ActionFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    status: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Action
        search_model_fields = ["name", "description"]

class CertificateTemplateFilter(Filter): 
    order_by: list[str] | None = ["template_name"]
    search: str | None = None
    template_name: str | None = None
    display_name: str | None = None
    enabled: bool | None = None
    client_authentication: bool | None = None
    enrollment_agent: bool | None = None
    any_purpose: bool | None = None
    enrollee_supplies_subject: bool | None = None
    requires_manager_approval: bool | None = None
    requires_manager_archival: bool | None = None
    authorized_signatures_required: int | None = None
    validity_period: str | None = None
    renewal_period: str | None = None
    minimum_rsa_key_length: int | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.CertificateTemplate
        search_model_fields = ['template_name', 'display_name', 'validity_period', 'renewal_period']


class CertificateAuthorityFilter(Filter): 
    order_by: list[str] | None = ["ca_name"]
    search: str | None = None
    ca_name: str | None = None
    dns_name: str | None = None
    certificate_subject: str | None = None
    certificate_serial_number: str | None = None
    certificate_validity_start: str | None = None
    certificate_validity_end: str | None = None
    web_enrollment: str | None = None
    user_specified_san: str | None = None
    request_disposition: str | None = None
    enforce_encryption_for_requests: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.CertificateAuthority
        search_model_fields = ['ca_name', 'dns_name', 'certificate_subject', 'certificate_serial_number', 'certificate_validity_start', 'certificate_validity_end', 'web_enrollment', 'user_specified_san', 'request_disposition', 'enforce_encryption_for_requests']


class IssueFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    name: str | None = None
    description: str | None = None
    impact: str | None = None
    exploitability: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Issue
        search_model_fields = ['name', 'description', 'impact', 'exploitability']


class TimeLineFilter(Filter): 
    order_by: list[str] | None = ["-time_completed"]
    search: str | None = None
    status: str | None = None

    class Constants(Filter.Constants):
        model = models.TimeLine
        search_model_fields = ['status']


class PlaybookFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    playbook_name: str | None = None
    description: str | None = None
    status: str | None = None
    steps: int | None = None
    completed: int | None = None
    playbook_template_id: str | UUID4 | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Playbook
        search_model_fields = ['playbook_name', 'description', 'status']


class ShareFileFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    type: str | None = None
    file_id: str | UUID4 | None = None
    parent_id: str | UUID4 | None = None
    share_id: str | UUID4 | None = None
    unc_path: str | None = None
    depth: int | None = None
    name: str | None = None
    downloaded: bool | None = None
    indexed: bool | None = None
    extension: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.ShareFile
        search_model_fields = ['type', 'unc_path', 'name']


class DomainFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    short_name: str | None = None
    long_name: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Domain
        search_model_fields = ['short_name', 'long_name']


class CredentialFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    domain_id: str | UUID4 | None = None
    username: str | None = None
    password_id: str | UUID4 | None = None
    kerberos_id: str | UUID4 | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))
    domain: DomainFilter | None = FilterDepends(with_prefix("domain", DomainFilter))

    class Constants(Filter.Constants):
        model = models.Credential
        search_model_fields = ['username']


class PasswordFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    password: str | None = None
    nt: str | None = None
    aes256_key: str | None = None
    aes128_key: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Password
        search_model_fields = ['password', 'nt', 'aes256_key', 'aes128_key']


class C2ServerTypeFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    name: str | None = None

    class Constants(Filter.Constants):
        model = models.C2ServerType
        search_model_fields = ['name']


class SituationalAwarenessFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    name: str | None = None
    category: str | None = None
    domain_id: str | UUID4 | None = None

    class Constants(Filter.Constants):
        model = models.SituationalAwareness
        search_model_fields = ['name', 'category', 'value_string']


class C2JobFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    status: str | None = None
    c2_type: str | None = None
    c2_task_id: str | UUID4 | None = None
    c2_server_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    command: str | None = None
    arguments: str | None = None
    playbook_id: str | UUID4 | None = None
    message: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.C2Job
        search_model_fields = ['status', 'c2_type', 'command', 'arguments', 'message']


class HighlightFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    file_id: str | UUID4 | None = None
    c2_task_id: str | UUID4 | None = None
    c2_task_output_id: str | UUID4 | None = None
    proxy_job_output_id: str | UUID4 | None = None
    proxy_job_id: str | UUID4 | None = None
    parse_result_id: str | UUID4 | None = None
    rule_id: int | None = None
    rule_type: str | None = None
    hit: str | None = None
    start: int | None = None
    end: int | None = None
    line: int | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Highlight
        search_model_fields = ['rule_type', 'hit']


class SuggestionFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    name: str | None = None
    reason: str | None = None
    playbook_template_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Suggestion
        search_model_fields = ['name', 'reason']


class ProxyFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    host: str | None = None
    port: int | None = None
    type: str | None = None
    status: str | None = None
    note: str | None = None
    remote_hostname: str | None = None
    username: str | None = None
    password: str | None = None
    c2_server_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    c2_task_id: str | UUID4 | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Proxy
        search_model_fields = ['host', 'type', 'status', 'note', 'remote_hostname']


class ChecklistFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    domain_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    phase: str | None = None
    name: str | None = None
    status: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Checklist
        search_model_fields = ['phase', 'name', 'status']


class ObjectivesFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Objectives
        search_model_fields = ['name', 'description', 'status']


class C2ServerFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    type: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.C2Server
        search_model_fields = ['name', 'hostname', 'username']
