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

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, validates
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column


class SituationalAwareness(Base):
    __tablename__ = "situational_awareness"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    value_string: Mapped[str] = mapped_column(String, nullable=True)
    value_int: Mapped[int] = mapped_column(Integer, nullable=True)
    value_bool: Mapped[bool] = mapped_column(Boolean, nullable=True)
    value_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    domain_id: Mapped[UUID] = mapped_column(ForeignKey("domains.id"), nullable=True)

    domain = relationship("Domain", lazy="joined")

    @validates("name", "category", "value_string")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")
        return None
