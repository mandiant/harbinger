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


from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict

from .label import Label


class LabeledItemBase(BaseModel):
    label_id: UUID4 | str
    domain_id: str | UUID4 | None = None
    password_id: str | UUID4 | None = None
    credential_id: str | UUID4 | None = None
    kerberos_id: str | UUID4 | None = None
    proxy_id: str | UUID4 | None = None
    proxy_job_id: str | UUID4 | None = None
    proxy_job_output: str | UUID4 | None = None
    file_id: str | UUID4 | None = None
    playbook_id: str | UUID4 | None = None
    playbook_step_id: str | UUID4 | None = None
    c2_job_id: str | UUID4 | None = None
    host_id: str | UUID4 | None = None
    process_id: str | UUID4 | None = None
    playbook_template_id: str | UUID4 | None = None
    c2_server_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    c2_task_id: str | UUID4 | None = None
    c2_task_output_id: str | UUID4 | None = None
    share_id: str | UUID4 | None = None
    share_file_id: str | UUID4 | None = None
    hash_id: str | UUID4 | None = None
    highlight_id: str | UUID4 | None = None
    parse_result_id: str | UUID4 | None = None
    socks_server_id: str | UUID4 | None = None
    action_id: str | UUID4 | None = None
    certificate_template_id: str | UUID4 | None = None
    certificate_authority_id: str | UUID4 | None = None
    manual_timeline_task_id: str | UUID4 | None = None
    suggestion_id: str | UUID4 | None = None
    plan_id: str | UUID4 | None = None
    plan_step_id: str | UUID4 | None = None


class LabeledItemCreate(LabeledItemBase):
    pass


class LabeledItemDelete(LabeledItemBase):
    label_id: UUID4 | str | None = None  # type: ignore


class LabeledItem(LabeledItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime | None = None
    label: Label | None = None
