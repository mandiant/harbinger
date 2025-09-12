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
from typing import TYPE_CHECKING

from pydantic import UUID4, BaseModel, ConfigDict

if TYPE_CHECKING:
    from .label import Label


class CertificateAuthorityBase(BaseModel):
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


class CertificateAuthorityCreate(CertificateAuthorityBase):
    pass


class CertificateAuthority(CertificateAuthorityBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    time_created: datetime | None = None
    time_updated: datetime | None = None

    labels: list["Label"] | None = None
