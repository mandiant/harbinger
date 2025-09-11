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

from typing import List

from pydantic import BaseModel


from .action import ActionCreate
from .c2_server import C2ServerCreate, C2ServerTypeYaml
from .file_config import FileConfig
from .label import LabelCreate
from .playbook_template import PlaybookTemplateCreate
from .setting import SettingCategoryCreate


class HarbingerYaml(BaseModel):
    files: List[FileConfig] | None = None
    c2_server_types: List[C2ServerTypeYaml] | None = None
    labels: List[LabelCreate] | None = None
    actions: List["ActionCreate"] | None = None
    setting_categories: List["SettingCategoryCreate"] | None = None
    playbooks: List["PlaybookTemplateCreate"] | None = None
    c2_servers: List["C2ServerCreate"] | None = None
