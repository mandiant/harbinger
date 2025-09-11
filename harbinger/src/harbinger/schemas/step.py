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


from pydantic import BaseModel


from .c2_job import C2Type
from .playbook_step import PlaybookStepModifierBase
from .step_argument import StepArgument


class Step(BaseModel):
    type: C2Type
    name: str
    args: list[StepArgument] | None = None
    delay: int | None = None
    label: str | None = ""
    depends_on: str | None = ""
    tmate: bool | None = True
    asciinema: bool | None = True
    proxychains: bool | None = True
    modifiers: list[PlaybookStepModifierBase] | None = None
