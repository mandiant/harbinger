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
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column

if TYPE_CHECKING:
    from .domain import Domain
    from .label import Label


class Host(Base):
    __tablename__ = "hosts"
    __table_args__ = (
        UniqueConstraint("domain_id", "name", name="domain_host_name_uc"),
    )
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    domain_id: Mapped[UUID] = mapped_column(ForeignKey("domains.id"), nullable=True)
    name: Mapped[str] = mapped_column(String)
    objectid: Mapped[str] = mapped_column(String, unique=True)
    owned: Mapped[bool] = mapped_column(Boolean)
    domain: Mapped[str] = mapped_column(String)
    fqdn: Mapped[str] = mapped_column(String, unique=True)

    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    domain_obj = relationship("Domain", lazy="joined")
