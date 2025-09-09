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
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, validates
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column

if TYPE_CHECKING:
    from .label import Label


class C2Output(Base):
    __tablename__ = "c2_task_output"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    c2_implant_id: Mapped[UUID] = mapped_column(ForeignKey("c2_implants.id"), nullable=True)
    c2_task_id: Mapped[UUID] = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)
    c2_server_id: Mapped[UUID] = mapped_column(ForeignKey("c2_servers.id"), nullable=True)
    internal_id: Mapped[str] = mapped_column(String)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    response_text: Mapped[str] = mapped_column(String)
    response_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    output_type: Mapped[str] = mapped_column(String, nullable=True)
    raw_json: Mapped[dict] = mapped_column(JSON)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    __table_args__ = (
        UniqueConstraint("c2_server_id", "internal_id", name="c2_output_uc"),
    )

    @validates("response_text", "output_type")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")
        return None
