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
from typing import List

from pydantic import (UUID4, BaseModel, ConfigDict)


from .label import Label


class CertificateTemplateBase(BaseModel):
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

class CertificateTemplateCreate(CertificateTemplateBase):
    certificate_authorities: list[str] | None = []

class CertificateTemplate(CertificateTemplateBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    time_created: datetime | None = None
    time_updated: datetime | None = None

    labels: List["Label"] | None = None

