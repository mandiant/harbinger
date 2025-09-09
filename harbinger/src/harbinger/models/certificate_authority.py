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

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column

if TYPE_CHECKING:
    from .label import Label


class CertificateAuthority(Base):
    __tablename__ = "certificate_authorities"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ca_name: Mapped[str] = mapped_column(String)
    dns_name: Mapped[str] = mapped_column(String)
    certificate_subject: Mapped[str] = mapped_column(String)
    certificate_serial_number: Mapped[str] = mapped_column(String)
    certificate_validity_start: Mapped[str] = mapped_column(String)
    certificate_validity_end: Mapped[str] = mapped_column(String)
    web_enrollment: Mapped[str] = mapped_column(String)
    user_specified_san: Mapped[str] = mapped_column(String)
    request_disposition: Mapped[str] = mapped_column(String)
    enforce_encryption_for_requests: Mapped[str] = mapped_column(String)

    time_created: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    __table_args__ = (UniqueConstraint("ca_name", "dns_name", name="ca_dns_name_uc"),)