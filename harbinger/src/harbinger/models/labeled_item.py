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

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from harbinger.database.database import Base
from harbinger.database.types import mapped_column

if TYPE_CHECKING:
    from .label import Label


class LabeledItem(Base):
    __tablename__ = "labeled_item"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    label_id: Mapped[UUID] = mapped_column(ForeignKey("labels.id"), nullable=False)
    domain_id: Mapped[UUID] = mapped_column(ForeignKey("domains.id"), nullable=True)
    password_id: Mapped[UUID] = mapped_column(ForeignKey("passwords.id"), nullable=True)
    kerberos_id: Mapped[UUID] = mapped_column(ForeignKey("kerberos.id"), nullable=True)
    credential_id: Mapped[UUID] = mapped_column(
        ForeignKey("credentials.id"), nullable=True
    )
    proxy_id: Mapped[UUID] = mapped_column(ForeignKey("proxies.id"), nullable=True)
    proxy_job_id: Mapped[UUID] = mapped_column(
        ForeignKey("proxy_jobs.id"), nullable=True
    )
    proxy_job_output: Mapped[UUID] = mapped_column(
        ForeignKey("proxy_job_output.id"), nullable=True
    )
    file_id: Mapped[UUID] = mapped_column(ForeignKey("files.id"), nullable=True)
    playbook_id: Mapped[UUID] = mapped_column(ForeignKey("playbooks.id"), nullable=True)
    playbook_step_id: Mapped[UUID] = mapped_column(
        ForeignKey("playbook_step.id"), nullable=True
    )
    c2_job_id: Mapped[UUID] = mapped_column(ForeignKey("c2_jobs.id"), nullable=True)
    host_id: Mapped[UUID] = mapped_column(ForeignKey("hosts.id"), nullable=True)
    process_id: Mapped[UUID] = mapped_column(ForeignKey("processes.id"), nullable=True)
    playbook_template_id: Mapped[UUID] = mapped_column(
        ForeignKey("playbook_templates.id"), nullable=True
    )
    c2_server_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_servers.id"), nullable=True
    )
    c2_implant_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_implants.id"), nullable=True
    )
    c2_task_id: Mapped[UUID] = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)
    c2_task_output_id: Mapped[UUID] = mapped_column(
        ForeignKey("c2_task_output.id"), nullable=True
    )
    time_created: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    share_id: Mapped[UUID] = mapped_column(ForeignKey("shares.id"), nullable=True)
    share_file_id: Mapped[UUID] = mapped_column(
        ForeignKey("share_files.id"), nullable=True
    )
    highlight_id: Mapped[UUID] = mapped_column(
        ForeignKey("highlights.id"), nullable=True
    )
    hash_id: Mapped[UUID] = mapped_column(ForeignKey("hashes.id"), nullable=True)
    parse_result_id: Mapped[UUID] = mapped_column(
        ForeignKey("parse_results.id"), nullable=True
    )
    socks_server_id: Mapped[UUID] = mapped_column(
        ForeignKey("socks_servers.id"), nullable=True
    )
    action_id: Mapped[UUID] = mapped_column(ForeignKey("actions.id"), nullable=True)
    certificate_authority_id: Mapped[UUID] = mapped_column(
        ForeignKey("certificate_authorities.id"), nullable=True
    )
    certificate_template_id: Mapped[UUID] = mapped_column(
        ForeignKey("certificate_templates.id"), nullable=True
    )
    issue_id: Mapped[UUID] = mapped_column(ForeignKey("issues.id"), nullable=True)
    manual_timeline_task_id: Mapped[UUID] = mapped_column(
        ForeignKey("manual_timeline_tasks.id"), nullable=True
    )
    suggestion_id: Mapped[UUID] = mapped_column(
        ForeignKey("suggestions.id"), nullable=True
    )
    checklist_id: Mapped[UUID] = mapped_column(
        ForeignKey("checklist.id"), nullable=True
    )
    objective_id: Mapped[UUID] = mapped_column(
        ForeignKey("objectives.id"), nullable=True
    )
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("plan.id"), nullable=True)
    plan_step_id: Mapped[UUID] = mapped_column(
        ForeignKey("plan_step.id"), nullable=True
    )

    label = relationship("Label", lazy="joined", viewonly=True)
