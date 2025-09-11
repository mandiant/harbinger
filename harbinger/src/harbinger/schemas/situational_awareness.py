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
from enum import Enum

from pydantic import UUID4, BaseModel, ConfigDict, model_validator


from .domain import Domain


class SANames(str, Enum):
    dns_server = "DNS Server"
    dns_server_ip = "DNS Server IP"
    domain_controller = "Domain Controller"
    domain_controller_ip = "Domain Controller IP"
    machine_account_quota = "Machine Account Quota"


class SACategories(str, Enum):
    domain = "Domain"
    host = "Host"


class SituationalAwarenessBase(BaseModel):
    name: str
    category: str
    value_string: str | None = None
    value_int: int | None = None
    value_bool: bool | None = None
    value_json: dict | None = None
    domain_id: str | UUID4 | None = None


class SituationalAwarenessCreate(SituationalAwarenessBase):
    @model_validator(mode="after")  # type: ignore
    def check_value_set(self) -> "SituationalAwarenessCreate":
        if not any(
            [
                self.value_string,
                self.value_bool,
                self.value_int is not None,
                self.value_json,
            ]
        ):
            raise ValueError("At least one value must be set")
        return self


class SituationalAwareness(SituationalAwarenessBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime
    domain: Domain | None = None
