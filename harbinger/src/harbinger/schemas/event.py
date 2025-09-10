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




class Streams(str, Enum):
    run_playbook = "run_playbook"
    run_c2_job = "run_c2_job"
    run_proxy_job = "run_proxy_job"
    proxy_job_output = "proxy_job_output"
    events = "app_events_stream"
    c2_server_events = "c2_server_events"


class EventType(str, Enum):
    new = "new"
    deleted = "deleted"
    status = "status"
    update = "update"


class Event(str, Enum):
    c2_implant = "c2_implant"
    c2_task = "c2_task"
    c2_task_output = "c2_task_output"
    c2_job_status = "c2_job_status"
    c2_job = "c2_job"
    c2_server = "c2_server"
    proxy_job_status = "proxy_job_status"
    domain = "domain"
    password = "password"
    credential = "credential"
    proxy = "proxy"
    proxy_job = "proxy_job"
    proxy_job_output = "proxy_job_output"
    component = "component"
    file = "file"
    playbook = "playbook"
    playbook_step = "playbook_step"
    process = "process"
    host = "host"
    suggestion = "suggestion"
    label = "label"
    labeled_item = "labeled_item"
    kerberos = "kerberos"
    situational_awareness = "situational_awareness"
    share = "share"
    share_file = "share_file"
    hash = "hash"
    certificate_template = "certificate_template"
    certificate_authority = "certificate_authority"
    certificate_template_permissions = "certificate_template_permissions"
    issue = "issue"
    action = "action"
    c2_server_type = "c2_server_type"
    progress = "progress"
    highlight = "highlight"
    checklist = "checklist"
    objective = "objective"
    playbook_template = "playbook_template"

