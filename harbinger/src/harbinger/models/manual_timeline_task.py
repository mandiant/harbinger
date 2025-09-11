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

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column
from .timeline import TimeLine

if TYPE_CHECKING:
    from .label import Label


class ManualTimelineTask(TimeLine):
    __tablename__ = "manual_timeline_tasks"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    status: Mapped[str] = mapped_column(String)
    arguments: Mapped[str] = mapped_column(String)
    time_started: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    time_completed: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    command_name: Mapped[str] = mapped_column(String)
    operator: Mapped[str] = mapped_column(String)
    output: Mapped[str] = mapped_column(String)
    hostname: Mapped[str] = mapped_column(String)
    ai_summary: Mapped[str] = mapped_column(String)
    processing_status: Mapped[str] = mapped_column(String)

    # For creating the timeline.
    argument_params = ""
    object_type = ""

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    __mapper_args__ = {
        "polymorphic_identity": "manual_timeline_tasks",
        "concrete": True,
    }
