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


from typing import TYPE_CHECKING

from pydantic import UUID4, BaseModel, ConfigDict

from .domain import Domain
from .kerberos import Kerberos
from .password import Password

if TYPE_CHECKING:
    from .label import Label


class CredentialBase(BaseModel):
    domain_id: str | UUID4 | None = None
    username: str
    password_id: UUID4 | None = None
    kerberos_id: UUID4 | None = None
    note: str | None = None


class CredentialCreate(CredentialBase):
    mark_owned: bool = True


class Credential(CredentialBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    domain: Domain | None = None
    password: Password | None = None
    kerberos: Kerberos | None = None
    labels: list["Label"] | None = None
