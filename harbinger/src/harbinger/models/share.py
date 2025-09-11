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

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, validates
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column

if TYPE_CHECKING:
    from .label import Label


class Share(Base):
    __tablename__ = "shares"
    __table_args__ = (UniqueConstraint("host_id", "name", name="share_host_name_uc"),)
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    host_id: Mapped[UUID] = mapped_column(ForeignKey("hosts.id"))
    name: Mapped[str] = mapped_column(String)
    unc_path: Mapped[str] = mapped_column(String)
    type: Mapped[int] = mapped_column(BigInteger)
    remark: Mapped[str] = mapped_column(String)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    @validates("name", "unc_path", "remark")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")
        return None
