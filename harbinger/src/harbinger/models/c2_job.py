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

from sqlalchemy import ARRAY, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column


class C2Job(Base):
    __tablename__ = "c2_jobs"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    status: Mapped[str] = mapped_column(String)
    c2_type: Mapped[str] = mapped_column(String)
    c2_task_id: Mapped[UUID] = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)
    c2_server_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_servers.id"),
        nullable=True,
    )
    c2_implant_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_implants.id"),
        nullable=True,
    )
    command: Mapped[str] = mapped_column(String)
    arguments: Mapped[str] = mapped_column(String)
    playbook_id: Mapped[UUID] = mapped_column(ForeignKey("playbooks.id"), nullable=True)

    message: Mapped[str] = mapped_column(String)

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
    add_labels: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)

    input_files = relationship(
        "File",
        secondary="input_files",
        lazy="joined",
        viewonly=True,
    )
    labels = relationship(
        "Label",
        secondary="labeled_item",
        lazy="joined",
        viewonly=True,
    )
