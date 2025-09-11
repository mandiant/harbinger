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


import builtins
import random
from typing import List, Literal
from uuid import uuid4

from pydantic import UUID4, BaseModel, ConfigDict, Field, create_model


from .argument import Argument, TypeEnum
from .label import Label


class PlaybookTemplateBase(BaseModel):
    icon: str = ""
    name: str = ""
    tactic: str | None = ""
    technique: str | None = ""
    args: list[Argument] | None = None
    steps: str | None = ""
    yaml: str = ""
    add_depends_on: bool | None = None


class PlaybookTemplateCreate(PlaybookTemplateBase):
    labels: list[str] | None = []
    id: UUID4 = Field(default_factory=uuid4)


class PlaybookTemplateView(PlaybookTemplateBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 = Field(default_factory=uuid4)
    labels: List["Label"] | None = []


class PlaybookTemplate(PlaybookTemplateCreate):
    model_config = ConfigDict(from_attributes=True)
    add_depends_on: bool | None = True

    def create_fields(self, default_arguments: dict | None = None) -> dict:
        result = {}
        for arg in self.args or []:
            default = arg.default
            options = arg.options or []
            if arg.required:
                default = ...  # type: ignore
            if default_arguments and arg.name in default_arguments:
                if (
                    type(default_arguments[arg.name]) == list
                    and default_arguments[arg.name]
                ):
                    options = default_arguments[arg.name]
                    arg.type = TypeEnum.options
                    default = options[0]
                else:
                    default = default_arguments[arg.name]
            if arg.type == TypeEnum.options:
                arg_type = Literal[tuple(options)]  # type: ignore
            else:
                arg_type = getattr(builtins, arg.type)
            result[arg.name] = (
                arg_type,
                Field(
                    default=default,
                    description=arg.description,
                    filetype=arg.filetype,  # type: ignore
                ),
            )
        return result

    def create_model(self, default_arguments: dict | None = None):
        return create_model(
            self.name,
            **self.create_fields(default_arguments),
        )


def create_random_color():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return "#{:02x}{:02x}{:02x}".format(int(r), int(g), int(b))


class PlaybookTemplateGenerated(BaseModel):
    icon: str
    name: str
    tactic: str
    technique: str
    args: list[Argument]
    steps: str
    add_depends_on: bool
