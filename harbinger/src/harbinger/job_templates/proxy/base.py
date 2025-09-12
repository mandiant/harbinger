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

from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger.job_templates.schemas import BaseTemplateModel, env


class JobTemplateModel(BaseTemplateModel):
    proxy_id: UUID4 | None = None
    socks_server_id: UUID4
    playbook_id: UUID4 | None = None

    async def generate_arguments(self, db: AsyncSession) -> str:
        objects = await self.resolve_objects(db)
        result = ""
        template = None
        if hasattr(self.Settings, "template") and self.Settings.template:
            template = env.get_template(self.Settings.template)
        elif hasattr(self.Settings, "template_str") and self.Settings.template_str:
            template = env.from_string(self.Settings.template_str)
        if template:
            result = await template.render_async(**self.model_dump(), **objects)
        return result

    async def generate_command(self) -> str:
        if hasattr(self.Settings, "command_str"):
            template = env.from_string(self.Settings.command_str)
            return await template.render_async(**self.model_dump())
        if hasattr(self.Settings, "command"):
            return self.Settings.command
        return ""

    class Settings:
        command = ""
        command_str = ""
        template = ""
        template_str = ""
        add_labels: list[str] = []
