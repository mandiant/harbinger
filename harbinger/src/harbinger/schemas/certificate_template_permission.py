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


class CertificateTemplatePermissionBase(BaseModel):
    certificate_template_id: str | UUID4 | None = None
    permission: str | None = None
    principal: str | None = None
    principal_type: str | None = None
    object_id: str | None = None


class CertificateTemplatePermissionCreate(CertificateTemplatePermissionBase):
    pass


class CertificateTemplatePermission(CertificateTemplatePermissionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    time_created: datetime | None = None
    time_updated: datetime | None = None
