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

import contextlib
import json
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import (
    UUID4,
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class TimeLineThemes(str, Enum):
    asciinema = "asciinema"
    dracula = "dracula"
    github_dark = "github_dark"
    github_light = "github-light"
    monokai = "monokai"
    nord = "nord"
    solarized_dark = "solarized-dark"
    solarized_light = "solarized-light"


class TimeLine(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    status: str | None = ""
    command_name: str | None = Field(
        validation_alias=AliasChoices("command_name", "command"),
        default="",
    )
    arguments: str | None = Field(
        validation_alias=AliasChoices("arguments", "display_params"),
        default="",
    )
    original_params: str | list | None = ""
    argument_params: str | list | None = ""
    operator: str | None = ""
    time_started: datetime | None = None
    time_completed: datetime | None = None
    hostname: str | None = ""
    object_type: str | None = ""
    output: str | None = ""
    ai_summary: str | None = ""
    processing_status: str | None = ""

    @field_validator("processing_status")
    @classmethod
    def set_processing_status(cls, processing_status):
        return processing_status or ""

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_hostname(cls, data: Any) -> Any:
        data.object_type = data.__class__.__name__
        if hasattr(data, "c2_implant") and data.c2_implant:
            data.hostname = data.c2_implant.hostname
        if hasattr(data, "proxy") and data.proxy:
            data.hostname = data.proxy.remote_hostname
        if hasattr(data, "original_params"):
            if data.original_params and "arguments" in data.original_params:
                with contextlib.suppress(json.decoder.JSONDecodeError):
                    data.argument_params = json.loads(data.original_params).get(
                        "arguments",
                        "",
                    )
        return data
