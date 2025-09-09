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

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column
from .timeline import TimeLine

if TYPE_CHECKING:
    from .credential import Credential
    from .proxy import Proxy
    from .file import File
    from .label import Label
    from .socks_server import SocksServer


class ProxyJob(TimeLine):
    __tablename__ = "proxy_jobs"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credential_id: Mapped[UUID] = mapped_column(ForeignKey("credentials.id"), nullable=True)
    proxy_id: Mapped[UUID] = mapped_column(ForeignKey("proxies.id"), nullable=True)
    socks_server_id: Mapped[UUID] = mapped_column(ForeignKey("socks_servers.id"), nullable=True)
    executor_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    exit_code: Mapped[int] = mapped_column(Integer)
    command: Mapped[str] = mapped_column(String)
    arguments: Mapped[str] = mapped_column(String)
    # input_files = mapped_column(ARRAY(String), nullable=True)
    playbook_id: Mapped[UUID] = mapped_column(ForeignKey("playbooks.id"), nullable=True)
    time_created: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    time_started: Mapped[DateTime] = mapped_column(DateTime(timezone=True))
    time_completed: Mapped[DateTime] = mapped_column(DateTime(timezone=True))

    tmate: Mapped[bool] = mapped_column(Boolean, default=True)
    asciinema: Mapped[bool] = mapped_column(Boolean, default=True)
    proxychains: Mapped[bool] = mapped_column(Boolean, default=True)
    env: Mapped[str] = mapped_column(String)
    ai_summary: Mapped[str] = mapped_column(String)
    processing_status: Mapped[str] = mapped_column(String)

    # for creating the timeline
    hostname = ""
    argument_params = ""
    object_type = ""

    credential = relationship("Credential", lazy="joined")
    proxy = relationship(
        "Proxy",
        lazy="joined",
        viewonly=True,
    )
    input_files = relationship(
        "File", secondary="input_files", lazy="joined", viewonly=True
    )
    files = relationship("File", back_populates="proxy_job", lazy="joined")
    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    socks_server = relationship(
        "SocksServer",
        lazy="joined",
        viewonly=True,
    )

    __mapper_args__ = {
        "polymorphic_identity": "proxy_job",
        "concrete": True,
    }