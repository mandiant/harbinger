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


from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict


class GraphNodeBase(BaseModel):
    node_type: str
    attributes: dict | str
    source: str | None = None
    graph_id: UUID4 | str


class GraphNodeCreate(GraphNodeBase):
    pass


class GraphNode(GraphNodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime
    time_updated: datetime | None = None
