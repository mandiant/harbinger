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


import random

from pydantic import UUID4, BaseModel, ConfigDict, field_validator


def create_random_color():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


class LabelBase(BaseModel):
    name: str
    category: str
    color: str | None = ""

    model_config = ConfigDict(validate_default=True)

    @field_validator("color")
    @classmethod
    def validate_color(cls, value):
        if not value:
            return create_random_color()
        return value


class LabelCreate(LabelBase):
    id: str | UUID4 | None = None


class Label(LabelBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4


class LabelView(BaseModel):
    category: str
    labels: list[Label]
