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

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, validates
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column

if TYPE_CHECKING:
    from .label import Label


class Highlight(Base):
    __tablename__ = "highlights"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    file_id: Mapped[UUID] = mapped_column(ForeignKey("files.id"))
    c2_task_id: Mapped[UUID] = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)
    c2_task_output_id: Mapped[UUID] = mapped_column(ForeignKey("c2_task_output.id"), nullable=True)
    proxy_job_output_id: Mapped[UUID] = mapped_column(
        ForeignKey("proxy_job_output.id"), nullable=True
    )
    proxy_job_id: Mapped[UUID] = mapped_column(ForeignKey("proxy_jobs.id"), nullable=True)
    parse_result_id: Mapped[UUID] = mapped_column(ForeignKey("parse_results.id"), nullable=True)
    rule_id: Mapped[int] = mapped_column(Integer)
    rule_type: Mapped[str] = mapped_column(String)
    hit: Mapped[str] = mapped_column(String)
    start: Mapped[int] = mapped_column(Integer)
    end: Mapped[int] = mapped_column(Integer)
    line: Mapped[int] = mapped_column(Integer)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    @validates("rule_type", "hit")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")
        return None