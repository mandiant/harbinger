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

import hashlib
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship, validates
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column

if TYPE_CHECKING:
    from .label import Label


def sha256(context):
    return hashlib.sha256(
        context.get_current_parameters()["hash"].encode("utf-8")
    ).hexdigest()


class Hash(Base):
    __tablename__ = "hashes"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    hash: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    hashcat_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String)
    sha256_hash: Mapped[str] = mapped_column(String, unique=True, default=sha256)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    @validates("hash", "type", "status")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")
        return None
