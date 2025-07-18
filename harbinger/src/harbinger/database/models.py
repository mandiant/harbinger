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

# mypy: ignore-errors
import uuid
import hashlib
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import (
    ARRAY,
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Interval,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import AbstractConcreteBase

from typing import Any, Optional, Type, TYPE_CHECKING, TypeVar, Union
from sqlalchemy.orm import Mapped
from sqlalchemy.types import TypeEngine
from .database import Base


_T = TypeVar("_T")

if TYPE_CHECKING:

    class mapped_column(Mapped[_T]):
        def __init__(
            self,
            __typ: Optional[Union[TypeEngine[_T], Type[TypeEngine[_T]], Any]],
            *arg,
            **kw,
        ): ...

else:
    mapped_column = Column


class User(SQLAlchemyBaseUserTableUUID, Base):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimeLine(AbstractConcreteBase, Base):
    strict_attrs = True
    time_started = mapped_column(DateTime(timezone=True))
    time_completed = mapped_column(DateTime(timezone=True))
    status = mapped_column(String)
    ai_summary = mapped_column(String)
    processing_status = mapped_column(String)


class Domain(Base):
    __tablename__ = "domains"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    short_name = mapped_column(String, unique=True)
    long_name = mapped_column(String, unique=True)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    @property
    def name(self) -> str:
        if self.long_name:
            return self.long_name
        elif self.short_name:
            return self.short_name
        return ""


class Password(Base):
    __tablename__ = "passwords"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    password = mapped_column(String)
    nt = mapped_column(String)
    aes256_key = mapped_column(String)
    aes128_key = mapped_column(String)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


class Kerberos(Base):
    __tablename__ = "kerberos"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client = mapped_column(String)
    server = mapped_column(String)
    key = mapped_column(String)
    keytype = mapped_column(String)
    auth = mapped_column(DateTime)
    start = mapped_column(DateTime)
    end = mapped_column(DateTime)
    renew = mapped_column(DateTime)
    ccache = mapped_column(String)
    kirbi = mapped_column(String)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


class Credential(Base):
    __tablename__ = "credentials"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_id = mapped_column(ForeignKey("domains.id"))
    username = mapped_column(String)
    password_id = mapped_column(ForeignKey("passwords.id"))
    kerberos_id = mapped_column(ForeignKey("kerberos.id"))
    note = mapped_column(String)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())

    domain = relationship(Domain, lazy="joined")
    password = relationship(Password, lazy="joined")
    kerberos = relationship(Kerberos, lazy="joined")
    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


class Proxy(Base):
    __tablename__ = "proxies"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host = mapped_column(String)
    port = mapped_column(Integer)
    type = mapped_column(String)
    status = mapped_column(String)
    note = mapped_column(String)
    remote_hostname = mapped_column(String)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    username = mapped_column(String)
    password = mapped_column(String)
    c2_server_id = mapped_column(ForeignKey("c2_servers.id"), nullable=True)
    internal_id = mapped_column(String)
    c2_implant_id = mapped_column(ForeignKey("c2_implants.id"), nullable=True)
    c2_task_id = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


class InputFile(Base):
    __tablename__ = "input_files"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = mapped_column(ForeignKey("files.id"))
    c2_job_id = mapped_column(ForeignKey("c2_jobs.id"), nullable=True)
    proxy_job_id = mapped_column(ForeignKey("proxy_jobs.id"), nullable=True)


class ProxyJob(TimeLine):
    __tablename__ = "proxy_jobs"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credential_id = mapped_column(ForeignKey("credentials.id"), nullable=True)
    proxy_id = mapped_column(ForeignKey("proxies.id"), nullable=True)
    socks_server_id = mapped_column(ForeignKey("socks_servers.id"), nullable=True)
    executor_type = mapped_column(String)
    status = mapped_column(String)
    exit_code = mapped_column(Integer)
    command = mapped_column(String)
    arguments = mapped_column(String)
    # input_files = mapped_column(ARRAY(String), nullable=True)
    playbook_id = mapped_column(ForeignKey("playbooks.id"), nullable=True)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())
    time_started = mapped_column(DateTime(timezone=True))
    time_completed = mapped_column(DateTime(timezone=True))

    tmate = mapped_column(Boolean, default=True)
    asciinema = mapped_column(Boolean, default=True)
    proxychains = mapped_column(Boolean, default=True)
    env = mapped_column(String)
    ai_summary = mapped_column(String)
    processing_status = mapped_column(String)

    # for creating the timeline
    hostname = ""
    argument_params = ""
    object_type = ""

    credential = relationship(Credential, lazy="joined")
    proxy = relationship(Proxy, lazy="joined")
    input_files = relationship(
        "File", secondary="input_files", lazy="joined", viewonly=True
    )
    files = relationship("File", back_populates="proxy_job", lazy="joined")
    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    proxy = relationship(
        "Proxy",
        lazy="joined",
        viewonly=True,
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


class Component(Base):
    __tablename__ = "components"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    hostname = mapped_column(String)
    status = mapped_column(String)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProxyJobOutput(Base):
    __tablename__ = "proxy_job_output"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = mapped_column(ForeignKey("proxy_jobs.id"), nullable=True)
    output = mapped_column(String)
    created_at = mapped_column(DateTime)
    output_type = mapped_column(String)

    proxy_job = relationship(ProxyJob)


class File(Base):
    __tablename__ = "files"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = mapped_column(ForeignKey("proxy_jobs.id"), nullable=True)
    filename = mapped_column(String)
    bucket = mapped_column(String)
    path = mapped_column(String)
    filetype = mapped_column(String)
    magic_mimetype = mapped_column(String)
    magika_mimetype = mapped_column(String)
    exiftool = mapped_column(String)
    md5sum = mapped_column(String)
    sha1sum = mapped_column(String)
    sha256sum = mapped_column(String)
    status = mapped_column(String)
    processing_status = mapped_column(String)
    processing_progress = mapped_column(Integer)
    processing_note = mapped_column(String)
    c2_implant_id = mapped_column(ForeignKey("c2_implants.id"), nullable=True)
    c2_task_id = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)
    manual_timeline_task_id = mapped_column(ForeignKey("manual_timeline_tasks.id"), nullable=True)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())

    proxy_job = relationship(ProxyJob, back_populates="files", lazy="joined")
    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


class Playbook(Base):
    __tablename__ = "playbooks"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    playbook_name = mapped_column(String)
    description = mapped_column(String)
    status = mapped_column(String)
    arguments = mapped_column(JSON)
    steps = mapped_column(Integer)
    completed = mapped_column(Integer)
    playbook_template_id = mapped_column(
        ForeignKey("playbook_templates.id"), nullable=True
    )

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())
    time_started = mapped_column(DateTime(timezone=True))
    time_completed = mapped_column(DateTime(timezone=True))
    graph = ""
    correct = True

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


class PlaybookStep(Base):
    __tablename__ = "playbook_step"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = mapped_column(Integer)
    label = mapped_column(String, default="")
    depends_on = mapped_column(String, default="")
    playbook_id = mapped_column(ForeignKey("playbooks.id"), nullable=True)
    proxy_job_id = mapped_column(ForeignKey("proxy_jobs.id"), nullable=True)
    c2_job_id = mapped_column(ForeignKey("c2_jobs.id"), nullable=True)
    status = mapped_column(String)
    delay = mapped_column(Interval, nullable=True)
    execute_after = mapped_column(DateTime(timezone=True), nullable=True)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())
    time_started = mapped_column(DateTime(timezone=True))
    time_completed = mapped_column(DateTime(timezone=True))

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    step_modifiers = relationship("PlaybookStepModifier", lazy="joined")


class PlaybookStepModifier(Base):
    __tablename__ = "playbook_step_modifier"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regex = mapped_column(String)
    input_path = mapped_column(String)
    output_path = mapped_column(String)
    output_format = mapped_column(String)
    status = mapped_column(String)
    on_error = mapped_column(String)
    data = mapped_column(String)
    status_message = mapped_column(String)
    playbook_step_id = mapped_column(ForeignKey("playbook_step.id"), nullable=True)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())


class C2Job(Base):
    __tablename__ = "c2_jobs"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = mapped_column(String)
    c2_type = mapped_column(String)
    c2_task_id = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)
    c2_server_id = mapped_column(ForeignKey("c2_servers.id"), nullable=True)
    c2_implant_id = mapped_column(ForeignKey("c2_implants.id"), nullable=True)
    command = mapped_column(String)
    arguments = mapped_column(String)
    playbook_id = mapped_column(ForeignKey("playbooks.id"), nullable=True)

    message = mapped_column(String)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())
    time_started = mapped_column(DateTime(timezone=True))
    time_completed = mapped_column(DateTime(timezone=True))
    add_labels = mapped_column(ARRAY(String), nullable=True)

    input_files = relationship(
        "File", secondary="input_files", lazy="joined", viewonly=True
    )
    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


class Host(Base):
    __tablename__ = "hosts"
    __table_args__ = (
        UniqueConstraint("domain_id", "name", name="domain_host_name_uc"),
    )
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_id = mapped_column(ForeignKey("domains.id"), nullable=True)
    name = mapped_column(String)
    objectid = mapped_column(String, unique=True)
    owned = mapped_column(Boolean)
    domain = mapped_column(String)
    fqdn = mapped_column(String, unique=True)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    domain_obj = relationship(Domain, lazy="joined")
    # ips = relationship("IpAddress", lazy="joined")
    # processes = relationship("Process", back_populates="host", lazy="joined")


class IpAddress(Base):
    __tablename__ = "ip_addresses"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    host_id = mapped_column(ForeignKey("hosts.id"), nullable=True)
    ip_address = mapped_column(String)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())


class Process(Base):
    __tablename__ = "processes"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    process_id = mapped_column(Integer)
    architecture = mapped_column(String)
    name = mapped_column(String)
    user = mapped_column(String)
    bin_path = mapped_column(String)
    parent_process_id = mapped_column(Integer)
    command_line = mapped_column(String)
    description = mapped_column(String)
    handle = mapped_column(String)
    host_id = mapped_column(ForeignKey("hosts.id"), nullable=True)
    number = mapped_column(Integer)
    c2_implant_id = mapped_column(ForeignKey("c2_implants.id"), nullable=True)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    # host = relationship(Host, back_populates="processes", lazy="joined")


class PlaybookTemplate(Base):
    __tablename__ = "playbook_templates"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    tactic = mapped_column(String)
    technique = mapped_column(String)
    icon = mapped_column(String)
    step_delay = mapped_column(Integer)
    yaml = mapped_column(String)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


class Label(Base):
    __tablename__ = "labels"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String, unique=True)
    category = mapped_column(String)
    color = mapped_column(String)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __str__(self):
        return f"Label: {self.name}"


class LabeledItem(Base):
    __tablename__ = "labeled_item"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label_id = mapped_column(ForeignKey("labels.id"), nullable=False)
    domain_id = mapped_column(ForeignKey("domains.id"), nullable=True)
    password_id = mapped_column(ForeignKey("passwords.id"), nullable=True)
    kerberos_id = mapped_column(ForeignKey("kerberos.id"), nullable=True)
    credential_id = mapped_column(ForeignKey("credentials.id"), nullable=True)
    proxy_id = mapped_column(ForeignKey("proxies.id"), nullable=True)
    proxy_job_id = mapped_column(ForeignKey("proxy_jobs.id"), nullable=True)
    proxy_job_output = mapped_column(ForeignKey("proxy_job_output.id"), nullable=True)
    file_id = mapped_column(ForeignKey("files.id"), nullable=True)
    playbook_id = mapped_column(ForeignKey("playbooks.id"), nullable=True)
    playbook_step_id = mapped_column(ForeignKey("playbook_step.id"), nullable=True)
    c2_job_id = mapped_column(ForeignKey("c2_jobs.id"), nullable=True)
    host_id = mapped_column(ForeignKey("hosts.id"), nullable=True)
    process_id = mapped_column(ForeignKey("processes.id"), nullable=True)
    playbook_template_id = mapped_column(
        ForeignKey("playbook_templates.id"), nullable=True
    )
    c2_server_id = mapped_column(ForeignKey("c2_servers.id"), nullable=True)
    c2_implant_id = mapped_column(ForeignKey("c2_implants.id"), nullable=True)
    c2_task_id = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)
    c2_task_output_id = mapped_column(ForeignKey("c2_task_output.id"), nullable=True)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    share_id = mapped_column(ForeignKey("shares.id"), nullable=True)
    share_file_id = mapped_column(ForeignKey("share_files.id"), nullable=True)
    highlight_id = mapped_column(ForeignKey("highlights.id"), nullable=True)
    hash_id = mapped_column(ForeignKey("hashes.id"), nullable=True)
    parse_result_id = mapped_column(ForeignKey("parse_results.id"), nullable=True)
    socks_server_id = mapped_column(ForeignKey("socks_servers.id"), nullable=True)
    action_id = mapped_column(ForeignKey("actions.id"), nullable=True)
    certificate_authority_id = mapped_column(
        ForeignKey("certificate_authorities.id"), nullable=True
    )
    certificate_template_id = mapped_column(
        ForeignKey("certificate_templates.id"), nullable=True
    )
    issue_id = mapped_column(ForeignKey("issues.id"), nullable=True)
    manual_timeline_task_id = mapped_column(
        ForeignKey("manual_timeline_tasks.id"), nullable=True
    )
    suggestion_id = mapped_column(ForeignKey("suggestions.id"), nullable=True)
    checklist_id = mapped_column(ForeignKey("checklist.id"), nullable=True)
    objective_id = mapped_column(ForeignKey("objectives.id"), nullable=True)

    label = relationship(Label, lazy="joined", viewonly=True)


class C2Server(Base):
    __tablename__ = "c2_servers"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = mapped_column(String)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    name = mapped_column(String)
    hostname = mapped_column(String)
    username = mapped_column(String)
    password = mapped_column(String)
    port = mapped_column(Integer)
    ca_certificate = mapped_column(String)
    certificate = mapped_column(String)
    private_key = mapped_column(String)
    token = mapped_column(String)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    status = relationship("C2ServerStatus", lazy="joined")


class C2ServerStatus(Base):
    __tablename__ = "c2_server_status"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    c2_server_id = mapped_column(ForeignKey("c2_servers.id"), nullable=True)
    name = mapped_column(String)
    status = mapped_column(String)
    message = mapped_column(String)

    def __str__(self):
        return f"{self.name}: {self.status}"


class C2Implant(Base):
    __tablename__ = "c2_implants"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    c2_server_id = mapped_column(ForeignKey("c2_servers.id"), nullable=True)
    internal_id = mapped_column(String)
    c2_type = mapped_column(String)
    payload_type = mapped_column(String)

    # Generalized data from the different c2s
    name = mapped_column(String)
    hostname = mapped_column(String)
    description = mapped_column(String)
    sleep = mapped_column(BigInteger)
    jitter = mapped_column(BigInteger)
    os = mapped_column(String)
    pid = mapped_column(Integer, nullable=True)
    architecture = mapped_column(String)
    process = mapped_column(String)
    username = mapped_column(String)
    ip = mapped_column(String)
    external_ip = mapped_column(String)
    domain = mapped_column(String)
    last_checkin = mapped_column(DateTime(timezone=True))

    # Also store the full data from the c2
    raw_json = mapped_column(JSON)

    # Host id
    host_id = mapped_column(ForeignKey("hosts.id"), nullable=True)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    __table_args__ = (
        UniqueConstraint("c2_server_id", "internal_id", name="c2_implants_uc"),
    )


class C2Task(TimeLine):
    __tablename__ = "c2_tasks"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    internal_id = mapped_column(String)
    c2_implant_id = mapped_column(ForeignKey("c2_implants.id"), nullable=True)
    c2_server_id = mapped_column(ForeignKey("c2_servers.id"), nullable=True)
    status = mapped_column(String)
    original_params = mapped_column(String)
    display_params = mapped_column(String)
    time_started = mapped_column(DateTime(timezone=True))
    time_completed = mapped_column(DateTime(timezone=True))
    command_name = mapped_column(String)
    operator = mapped_column(String)
    raw_json = mapped_column(JSON)
    ai_summary = mapped_column(String)
    processing_status = mapped_column(String)

    # For creating the timeline.
    hostname = ""
    argument_params = ""
    object_type = ""

    c2_implant = relationship(C2Implant, lazy="select")

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    __table_args__ = (
        UniqueConstraint("c2_server_id", "internal_id", name="c2_tasks_uc"),
    )
    __mapper_args__ = {
        "polymorphic_identity": "c2_tasks",
        "concrete": True,
    }

    @validates(
        "command_name", "original_params", "display_params", "status", "operator"
    )
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")


class C2Output(Base):
    __tablename__ = "c2_task_output"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())
    c2_implant_id = mapped_column(ForeignKey("c2_implants.id"), nullable=True)
    c2_task_id = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)
    c2_server_id = mapped_column(ForeignKey("c2_servers.id"), nullable=True)
    internal_id = mapped_column(String)
    timestamp = mapped_column(DateTime(timezone=True))
    response_text = mapped_column(String)
    response_bytes = mapped_column(LargeBinary)
    output_type = mapped_column(String, nullable=True)
    raw_json = mapped_column(JSON)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    __table_args__ = (
        UniqueConstraint("c2_server_id", "internal_id", name="c2_output_uc"),
    )

    @validates("response_text", "output_type")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")


class SituationalAwareness(Base):
    __tablename__ = "situational_awareness"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    name = mapped_column(String)
    category = mapped_column(String)
    value_string = mapped_column(String, nullable=True)
    value_int = mapped_column(Integer, nullable=True)
    value_bool = mapped_column(Boolean, nullable=True)
    value_json = mapped_column(JSON, nullable=True)
    domain_id = mapped_column(ForeignKey("domains.id"), nullable=True)

    domain = relationship(Domain, lazy="joined")

    @validates("name", "category", "value_string")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")


class Share(Base):
    __tablename__ = "shares"
    __table_args__ = (UniqueConstraint("host_id", "name", name="share_host_name_uc"),)
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    host_id = mapped_column(ForeignKey("hosts.id"))
    name = mapped_column(String)
    unc_path = mapped_column(String)
    type = mapped_column(BigInteger)
    remark = mapped_column(String)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    @validates("name", "unc_path", "remark")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")


class ShareFile(Base):
    __tablename__ = "share_files"
    __table_args__ = (UniqueConstraint("unc_path", name="share_files_unc_path"),)
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    type = mapped_column(String)
    file_id = mapped_column(ForeignKey("files.id"), nullable=True)
    parent_id = mapped_column(ForeignKey("share_files.id"), nullable=True)
    share_id = mapped_column(ForeignKey("shares.id"))
    size = mapped_column(BigInteger)
    last_accessed = mapped_column(DateTime)
    last_modified = mapped_column(DateTime)
    created = mapped_column(DateTime)
    unc_path = mapped_column(String)
    depth = mapped_column(Integer)
    name = mapped_column(String)
    extension = mapped_column(String)
    downloaded = mapped_column(Boolean, default=False)
    indexed = mapped_column(Boolean, default=False)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    @validates("unc_path", "name")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")


class Highlight(Base):
    __tablename__ = "highlights"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    file_id = mapped_column(ForeignKey("files.id"))
    c2_task_id = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)
    c2_task_output_id = mapped_column(ForeignKey("c2_task_output.id"), nullable=True)
    proxy_job_output_id = mapped_column(
        ForeignKey("proxy_job_output.id"), nullable=True
    )
    proxy_job_id = mapped_column(ForeignKey("proxy_jobs.id"), nullable=True)
    parse_result_id = mapped_column(ForeignKey("parse_results.id"), nullable=True)
    rule_id = mapped_column(Integer)
    rule_type = mapped_column(String)
    hit = mapped_column(String)
    start = mapped_column(Integer)
    end = mapped_column(Integer)
    line = mapped_column(Integer)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    @validates("rule_type", "hit")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")


def sha256(context):
    return hashlib.sha256(
        context.get_current_parameters()["hash"].encode("utf-8")
    ).hexdigest()


class Hash(Base):
    __tablename__ = "hashes"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    hash = mapped_column(String)
    type = mapped_column(String)
    hashcat_id = mapped_column(Integer)
    status = mapped_column(String)
    sha256_hash = mapped_column(String, unique=True, default=sha256)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    @validates("hash", "type", "status")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")


class ParseResult(Base):
    __tablename__ = "parse_results"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    file_id = mapped_column(ForeignKey("files.id"), nullable=True)
    parser = mapped_column(String)
    log = mapped_column(String)
    c2_task_id = mapped_column(ForeignKey("c2_tasks.id"), nullable=True)
    c2_task_output_id = mapped_column(ForeignKey("c2_task_output.id"), nullable=True)
    proxy_job_output_id = mapped_column(
        ForeignKey("proxy_job_output.id"), nullable=True
    )
    proxy_job_id = mapped_column(ForeignKey("proxy_jobs.id"), nullable=True)

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    @validates("parser", "log")
    def remove_nullbytes(self, key, value) -> str | None:
        if value:
            return value.replace("\x00", "")


class SettingCategory(Base):
    __tablename__ = "setting_category"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String, unique=True)
    description = mapped_column(String)
    icon = mapped_column(String)
    order = mapped_column(Integer)


class Setting(Base):
    __tablename__ = "settings"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    category_id = mapped_column(ForeignKey("setting_category.id"), nullable=False)
    type = mapped_column(String)
    description = mapped_column(String)
    value = mapped_column(JSON)
    __table_args__ = (UniqueConstraint("name", "category_id", name="name_category"),)


class SocksServer(Base):
    __tablename__ = "socks_servers"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = mapped_column(String)
    hostname = mapped_column(String)
    operating_system = mapped_column(String)
    status = mapped_column(String)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


class ActionPlaybook(Base):
    __tablename__ = "action_playbook"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_id = mapped_column(ForeignKey("actions.id"), nullable=False)
    playbook_template_id = mapped_column(
        ForeignKey("playbook_templates.id"), nullable=False
    )


class Action(Base):
    __tablename__ = "actions"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    description = mapped_column(String)
    status = mapped_column(String)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())
    time_started = mapped_column(DateTime(timezone=True))
    time_completed = mapped_column(DateTime(timezone=True))

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    playbook_templates = relationship(
        "PlaybookTemplate", secondary="action_playbook", lazy="joined", viewonly=True
    )


class CertificateAuthority(Base):
    __tablename__ = "certificate_authorities"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ca_name = mapped_column(String)
    dns_name = mapped_column(String)
    certificate_subject = mapped_column(String)
    certificate_serial_number = mapped_column(String)
    certificate_validity_start = mapped_column(String)
    certificate_validity_end = mapped_column(String)
    web_enrollment = mapped_column(String)
    user_specified_san = mapped_column(String)
    request_disposition = mapped_column(String)
    enforce_encryption_for_requests = mapped_column(String)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    __table_args__ = (UniqueConstraint("ca_name", "dns_name", name="ca_dns_name_uc"),)


class CertificateTemplate(Base):
    __tablename__ = "certificate_templates"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_name = mapped_column(String)
    display_name = mapped_column(String)
    enabled = mapped_column(Boolean)
    client_authentication = mapped_column(Boolean)
    enrollment_agent = mapped_column(Boolean)
    any_purpose = mapped_column(Boolean)
    enrollee_supplies_subject = mapped_column(Boolean)
    requires_manager_approval = mapped_column(Boolean)
    requires_manager_archival = mapped_column(Boolean)
    authorized_signatures_required = mapped_column(Integer)
    validity_period = mapped_column(String)
    renewal_period = mapped_column(String)
    minimum_rsa_key_length = mapped_column(Integer)
    raw_json = mapped_column(JSON)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )
    certificate_authorities = relationship(
        "CertificateAuthority",
        secondary="certificate_template_authority_map",
        lazy="joined",
        viewonly=True,
    )


class CertificateAuthorityMap(Base):
    __tablename__ = "certificate_template_authority_map"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    certificate_authority_id = mapped_column(
        ForeignKey("certificate_authorities.id"), nullable=False
    )
    certificate_template_id = mapped_column(
        ForeignKey("certificate_templates.id"), nullable=False
    )
    __table_args__ = (
        UniqueConstraint(
            "certificate_authority_id",
            "certificate_template_id",
            name="authority_template_id_uc",
        ),
    )


class CertificateTemplatePermission(Base):
    __tablename__ = "certificate_template_permissions"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    certificate_template_id = mapped_column(
        ForeignKey("certificate_templates.id"), nullable=False
    )
    permission = mapped_column(String)
    principal = mapped_column(String)
    principal_type = mapped_column(String)
    object_id = mapped_column(String)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())
    __table_args__ = (
        UniqueConstraint(
            "certificate_template_id",
            "permission",
            "principal",
            name="certificate_template_permissions_uc",
        ),
    )


class Issue(Base):
    __tablename__ = "issues"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String, unique=True)
    description = mapped_column(String)
    impact = mapped_column(String)
    exploitability = mapped_column(String)
    label_id = mapped_column(ForeignKey("labels.id"))

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


class ManualTimelineTask(TimeLine):
    __tablename__ = "manual_timeline_tasks"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    status = mapped_column(String)
    arguments = mapped_column(String)
    time_started = mapped_column(DateTime(timezone=True))
    time_completed = mapped_column(DateTime(timezone=True))
    command_name = mapped_column(String)
    operator = mapped_column(String)
    output = mapped_column(String)
    hostname = mapped_column(String)
    ai_summary = mapped_column(String)
    processing_status = mapped_column(String)

    # For creating the timeline.
    argument_params = ""
    object_type = ""

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    __mapper_args__ = {
        "polymorphic_identity": "manual_timeline_tasks",
        "concrete": True,
    }


class C2ServerType(Base):
    __tablename__ = "c2_server_types"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    docker_image = mapped_column(String)
    command = mapped_column(String)
    icon = mapped_column(String)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())

    arguments = relationship("C2ServerArguments", lazy="joined", viewonly=True)


class C2ServerArguments(Base):
    __tablename__ = "c2_server_arguments"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    regex = mapped_column(String)
    error = mapped_column(String)
    default = mapped_column(String)
    type = mapped_column(String)
    c2_server_type_id = mapped_column(ForeignKey("c2_server_types.id"), nullable=False)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())


class C2ImplantType(Base):
    __tablename__ = "c2_implant_types"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    c2_server_type_id = mapped_column(ForeignKey("c2_server_types.id"), nullable=False)
    icon = mapped_column(String)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())


class C2ImplantArguments(Base):
    __tablename__ = "c2_implant_arguments"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    c2_implant_type_id = mapped_column(
        ForeignKey("c2_implant_types.id"), nullable=False
    )

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())


class Suggestion(Base):
    __tablename__ = "suggestions"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    reason = mapped_column(String)
    playbook_template_id = mapped_column(
        ForeignKey("playbook_templates.id"), nullable=True
    )
    c2_implant_id = mapped_column(ForeignKey("c2_implants.id"), nullable=True)

    command = mapped_column(String)
    arguments = mapped_column(JSON)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


class Checklist(Base):
    __tablename__ = "checklist"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain_id = mapped_column(ForeignKey("domains.id"), nullable=True)
    c2_implant_id = mapped_column(ForeignKey("c2_implants.id"), nullable=True)
    phase = mapped_column(String)
    name = mapped_column(String)
    status = mapped_column(String)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )

    __table_args__ = (
        UniqueConstraint(
            "domain_id", "phase", "name", name="checklist_domain_phase_name"
        ),
        UniqueConstraint(
            "c2_implant_id", "phase", "name", name="checklist_implant_phase_name"
        ),
    )


class Objectives(Base):
    __tablename__ = "objectives"
    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = mapped_column(String)
    description = mapped_column(String)
    status = mapped_column(String)

    time_created = mapped_column(DateTime(timezone=True), server_default=func.now())
    time_updated = mapped_column(DateTime(timezone=True), onupdate=func.now())

    labels = relationship(
        "Label", secondary="labeled_item", lazy="joined", viewonly=True
    )


Base.registry.configure()
