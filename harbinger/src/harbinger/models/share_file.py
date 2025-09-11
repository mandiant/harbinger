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
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, validates
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column

if TYPE_CHECKING:
    from .label import Label


class ShareFile(Base):
    __tablename__ = "share_files"
    __table_args__ = (UniqueConstraint("unc_path", name="share_files_unc_path"),)
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    type: Mapped[str] = mapped_column(String)
    file_id: Mapped[UUID] = mapped_column(ForeignKey("files.id"), nullable=True)
    parent_id: Mapped[UUID] = mapped_column(ForeignKey("share_files.id"), nullable=True)
    share_id: Mapped[UUID] = mapped_column(ForeignKey("shares.id"))
    size: Mapped[int] = mapped_column(BigInteger)
    last_accessed: Mapped[DateTime] = mapped_column(DateTime)
    last_modified: Mapped[DateTime] = mapped_column(DateTime)
    created: Mapped[DateTime] = mapped_column(DateTime)
    unc_path: Mapped[str] = mapped_column(String)
    depth: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String)
    extension: Mapped[str] = mapped_column(String)
    downloaded: Mapped[bool] = mapped_column(Boolean, default=False)
    indexed: Mapped[bool] = mapped_column(Boolean, default=False)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    @validates("unc_path", "name")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")
        return None
