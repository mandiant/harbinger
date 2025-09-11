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

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, validates
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column
from .timeline import TimeLine

if TYPE_CHECKING:
    from .c2_implant import C2Implant
    from .label import Label


class C2Task(TimeLine):
    __tablename__ = "c2_tasks"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    internal_id: Mapped[str] = mapped_column(String)
    c2_implant_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_implants.id"), nullable=True
    )
    c2_server_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_servers.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String)
    original_params: Mapped[str] = mapped_column(String)
    display_params: Mapped[str] = mapped_column(String)
    time_started: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    time_completed: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    command_name: Mapped[str] = mapped_column(String)
    operator: Mapped[str] = mapped_column(String)
    raw_json: Mapped[dict] = mapped_column(JSON)
    ai_summary: Mapped[str] = mapped_column(String)
    processing_status: Mapped[str] = mapped_column(String)

    # For creating the timeline.
    hostname = ""
    argument_params = ""
    object_type = ""

    c2_implant = relationship("C2Implant", lazy="select")

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    __table_args__ = (
        UniqueConstraint("c2_server_id", "internal_id", name="c2_tasks_uc"),
    )
    __mapper_args__ = {
        "polymorphic_identity": "c2_tasks",
        "concrete": True,
    }

    @validates(
        "command_name", "original_params", "display_params", "status", "operator"
    )
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")
        return None
