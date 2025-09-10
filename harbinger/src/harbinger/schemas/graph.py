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

from pydantic import (UUID4, BaseModel, ConfigDict)


from .label import Label


class GraphBase(BaseModel):
    name: str
    description: str | None = None

class GraphCreate(GraphBase):
    pass

class Graph(GraphBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

    labels: List["Label"] | None = None

