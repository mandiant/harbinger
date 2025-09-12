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

from sqlalchemy import DateTime, ForeignKey, Integer, Interval, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column


class PlaybookStep(Base):
    __tablename__ = "playbook_step"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    number: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String, default="")
    depends_on: Mapped[str] = mapped_column(String, default="")
    playbook_id: Mapped[UUID] = mapped_column(ForeignKey("playbooks.id"), nullable=True)
    proxy_job_id: Mapped[UUID] = mapped_column(
        ForeignKey("proxy_jobs.id"),
        nullable=True,
    )
    c2_job_id: Mapped[UUID] = mapped_column(ForeignKey("c2_jobs.id"), nullable=True)
    status: Mapped[str] = mapped_column(String)
    delay: Mapped[Interval] = mapped_column(Interval, nullable=True)
    execute_after: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    time_updated: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )
    time_started: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    time_completed: Mapped[DateTime] = mapped_column(DateTime(timezone=True))

    labels = relationship(
        "Label",
        secondary="labeled_item",
        lazy="joined",
        viewonly=True,
    )
    step_modifiers = relationship("PlaybookStepModifier", lazy="joined")
