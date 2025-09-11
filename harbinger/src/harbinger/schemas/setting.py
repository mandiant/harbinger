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


from typing import Any

from pydantic import UUID4, BaseModel, ConfigDict


class SettingBase(BaseModel):
    name: str
    type: str
    description: str
    category_id: UUID4
    value: Any


class SettingCreate(SettingBase):
    category_id: UUID4 | None | str = ""


class Setting(SettingBase):
    id: UUID4
    model_config = ConfigDict(from_attributes=True)


class SettingCategoryBase(BaseModel):
    name: str
    description: str
    icon: str
    order: int


class SettingCategoryCreate(SettingCategoryBase):
    settings: list[SettingCreate]


class SettingCategory(SettingCategoryBase):
    id: UUID4
    model_config = ConfigDict(from_attributes=True)


class SettingModify(BaseModel):
    value: Any


class Settings(SettingCategoryBase):
    settings: list[Setting]
