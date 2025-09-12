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


class C2ServerArguments(Base):
    __tablename__ = "c2_server_arguments"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String)
    regex: Mapped[str] = mapped_column(String)
    error: Mapped[str] = mapped_column(String)
    default: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    c2_server_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_server_types.id"),
        nullable=False,
    )

    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    time_updated: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )
