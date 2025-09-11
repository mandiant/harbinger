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

from pydantic import BaseModel


class ArgumentNameEnum(str, Enum):
    hostname = "hostname"
    username = "username"
    password = "password"
    ca_certificate = "ca_certificate"
    certificate = "certificate"
    private_key = "private_key"
    token = "token"
    port = "port"


class RequiredArgument(BaseModel):
    name: ArgumentNameEnum
    regex: str | None = ""
    default: str | int | None = None
    error: str | None = "Please fill in this value"
    type: str | None = None

    def default_type(self) -> str | None:
        match self.name:
            case (
                ArgumentNameEnum.ca_certificate
                | ArgumentNameEnum.certificate
                | ArgumentNameEnum.private_key
            ):
                return "textarea"
            case ArgumentNameEnum.port:
                return "number"
            case (
                ArgumentNameEnum.hostname
                | ArgumentNameEnum.username
                | ArgumentNameEnum.password
                | ArgumentNameEnum.token
            ):
                return "text"
            case _:
                return None
