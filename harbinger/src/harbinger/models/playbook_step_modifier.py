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

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column


class PlaybookStepModifier(Base):
    __tablename__ = "playbook_step_modifier"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regex: Mapped[str] = mapped_column(String)
    input_path: Mapped[str] = mapped_column(String)
    output_path: Mapped[str] = mapped_column(String)
    output_format: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    on_error: Mapped[str] = mapped_column(String)
    data: Mapped[str] = mapped_column(String)
    status_message: Mapped[str] = mapped_column(String)
    playbook_step_id: Mapped[UUID] = mapped_column(ForeignKey("playbook_step.id"), nullable=True)
    time_created: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
