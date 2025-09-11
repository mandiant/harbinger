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
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column

if TYPE_CHECKING:
    from .label import Label


class Proxy(Base):
    __tablename__ = "proxies"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    host: Mapped[str] = mapped_column(String)
    port: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    note: Mapped[str] = mapped_column(String)
    remote_hostname: Mapped[str] = mapped_column(String)
    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    username: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(String)
    c2_server_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_servers.id"), nullable=True
    )
    internal_id: Mapped[str] = mapped_column(String)
    c2_implant_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_implants.id"), nullable=True
    )
    c2_task_id: Mapped[UUID] = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
