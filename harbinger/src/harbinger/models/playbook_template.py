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

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from harbinger.database.database import Base
from harbinger.database.types import mapped_column

if TYPE_CHECKING:
    from .label import Label


class PlaybookTemplate(Base):
    __tablename__ = "playbook_templates"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    tactic: Mapped[str] = mapped_column(String)
    technique: Mapped[str] = mapped_column(String)
    icon: Mapped[str] = mapped_column(String)
    step_delay: Mapped[int] = mapped_column(Integer)
    yaml: Mapped[str] = mapped_column(String)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )