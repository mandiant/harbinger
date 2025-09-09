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

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped

from harbinger.database.database import Base
from harbinger.database.types import mapped_column


class Setting(Base):
    __tablename__ = "settings"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    category_id: Mapped[UUID] = mapped_column(ForeignKey("setting_category.id"), nullable=False)
    type: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    value: Mapped[dict] = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("name", "category_id", name="name_category"),)

