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

import uuid

from pydantic import (BaseModel, ConfigDict, model_validator)
from typing_extensions import Self



class ProgressBar(BaseModel):
    current: int = 0
    max: int = 100
    percentage: float = 0.0
    type: str = ""
    id: str = ""
    description: str = ""

    model_config = ConfigDict(validate_default=True)

    @model_validator(mode='after')
    def validate_percentage(self) -> Self:
        self.percentage = self.current / self.max
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    def increase(self, step: int = 0):
        self.current += step
        self.percentage = self.current / self.max

