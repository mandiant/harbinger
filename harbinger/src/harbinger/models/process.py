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

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship

from harbinger.database.database import Base
from harbinger.database.types import mapped_column

if TYPE_CHECKING:
    from .label import Label


class Process(Base):
    __tablename__ = "processes"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    process_id: Mapped[int] = mapped_column(Integer)
    architecture: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    user: Mapped[str] = mapped_column(String)
    bin_path: Mapped[str] = mapped_column(String)
    parent_process_id: Mapped[int] = mapped_column(Integer)
    command_line: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    handle: Mapped[str] = mapped_column(String)
    host_id: Mapped[UUID] = mapped_column(ForeignKey("hosts.id"), nullable=True)
    number: Mapped[int] = mapped_column(Integer)
    c2_implant_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_implants.id"), nullable=True
    )

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
