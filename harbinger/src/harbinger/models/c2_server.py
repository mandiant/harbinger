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

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column


class C2Server(Base):
    __tablename__ = "c2_servers"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    type: Mapped[str] = mapped_column(String)
    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    name: Mapped[str] = mapped_column(String)
    hostname: Mapped[str] = mapped_column(String)
    username: Mapped[str] = mapped_column(String)
    password: Mapped[str] = mapped_column(String)
    port: Mapped[int] = mapped_column(Integer)
    ca_certificate: Mapped[str] = mapped_column(String)
    certificate: Mapped[str] = mapped_column(String)
    private_key: Mapped[str] = mapped_column(String)
    token: Mapped[str] = mapped_column(String)

    labels = relationship(
        "Label",
        secondary="labeled_item",
        lazy="joined",
        viewonly=True,
    )
    status = relationship("C2ServerStatus", lazy="joined")
