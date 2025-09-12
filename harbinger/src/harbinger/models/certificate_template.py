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

from sqlalchemy import JSON, Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column


class CertificateTemplate(Base):
    __tablename__ = "certificate_templates"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    template_name: Mapped[str] = mapped_column(String)
    display_name: Mapped[str] = mapped_column(String)
    enabled: Mapped[bool] = mapped_column(Boolean)
    client_authentication: Mapped[bool] = mapped_column(Boolean)
    enrollment_agent: Mapped[bool] = mapped_column(Boolean)
    any_purpose: Mapped[bool] = mapped_column(Boolean)
    enrollee_supplies_subject: Mapped[bool] = mapped_column(Boolean)
    requires_manager_approval: Mapped[bool] = mapped_column(Boolean)
    requires_manager_archival: Mapped[bool] = mapped_column(Boolean)
    authorized_signatures_required: Mapped[int] = mapped_column(Integer)
    validity_period: Mapped[str] = mapped_column(String)
    renewal_period: Mapped[str] = mapped_column(String)
    minimum_rsa_key_length: Mapped[int] = mapped_column(Integer)
    raw_json: Mapped[dict] = mapped_column(JSON)

    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    time_updated: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    labels = relationship(
        "Label",
        secondary="labeled_item",
        lazy="joined",
        viewonly=True,
    )
    certificate_authorities = relationship(
        "CertificateAuthority",
        secondary="certificate_template_authority_map",
        lazy="joined",
        viewonly=True,
    )
