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


class KerberosBase(BaseModel):
    client: str = ""
    server: str = ""
    key: str = ""
    keytype: str = ""
    auth: datetime | None = None
    start: datetime | None = None
    end: datetime | None = None
    renew: datetime | None = None
    ccache: str = ""
    kirbi: str = ""


class KerberosCreate(KerberosBase):
    pass


class Kerberos(KerberosBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: list["Label"] | None = None
