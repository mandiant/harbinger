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

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column


class C2Implant(Base):
    __tablename__ = "c2_implants"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    c2_server_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_servers.id"),
        nullable=True,
    )
    internal_id: Mapped[str] = mapped_column(String)
    c2_type: Mapped[str] = mapped_column(String)
    payload_type: Mapped[str] = mapped_column(String)

    # Generalized data from the different c2s
    name: Mapped[str] = mapped_column(String)
    hostname: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    sleep: Mapped[int] = mapped_column(BigInteger)
    jitter: Mapped[int] = mapped_column(BigInteger)
    os: Mapped[str] = mapped_column(String)
    pid: Mapped[int] = mapped_column(Integer, nullable=True)
    architecture: Mapped[str] = mapped_column(String)
    process: Mapped[str] = mapped_column(String)
    username: Mapped[str] = mapped_column(String)
    ip: Mapped[str] = mapped_column(String)
    external_ip: Mapped[str] = mapped_column(String)
    domain: Mapped[str] = mapped_column(String)
    last_checkin: Mapped[DateTime] = mapped_column(DateTime(timezone=True))

    # Also store the full data from the c2
    raw_json: Mapped[dict] = mapped_column(JSON)

    # Host id
    host_id: Mapped[UUID] = mapped_column(ForeignKey("hosts.id"), nullable=True)

    labels = relationship(
        "Label",
        secondary="labeled_item",
        lazy="joined",
        viewonly=True,
    )
    __table_args__ = (UniqueConstraint("c2_server_id", "internal_id", name="c2_implants_uc"),)
