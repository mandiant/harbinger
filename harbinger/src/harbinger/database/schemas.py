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

import builtins
import json
import uuid
import ntpath
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, List, Literal, Optional
from uuid import uuid4
from fastapi_users import schemas
from harbinger.graph.schemas import Edge, Node
from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    create_model,
    AliasChoices,
    field_validator,
    model_validator,
)
from typing_extensions import Self
import random


class Streams(str, Enum):
    run_playbook = "run_playbook"
    run_c2_job = "run_c2_job"
    run_proxy_job = "run_proxy_job"
    proxy_job_output = "proxy_job_output"
    events = "app_events_stream"
    c2_server_events = "c2_server_events"


class Event(str, Enum):
    c2_implant = "c2_implant"
    c2_task = "c2_task"
    c2_task_output = "c2_task_output"
    c2_job_status = "c2_job_status"
    c2_job = "c2_job"
    c2_server = "c2_server"
    proxy_job_status = "proxy_job_status"
    domain = "domain"
    password = "password"
    credential = "credential"
    proxy = "proxy"
    proxy_job = "proxy_job"
    proxy_job_output = "proxy_job_output"
    component = "component"
    file = "file"
    playbook = "playbook"
    playbook_step = "playbook_step"
    process = "process"
    host = "host"
    suggestion = "suggestion"
    label = "label"
    labeled_item = "labeled_item"
    kerberos = "kerberos"
    situational_awareness = "situational_awareness"
    share = "share"
    share_file = "share_file"
    hash = "hash"
    certificate_template = "certificate_template"
    certificate_authority = "certificate_authority"
    certificate_template_permissions = "certificate_template_permissions"
    issue = "issue"
    action = "action"
    c2_server_type = "c2_server_type"
    progress = "progress"
    highlight = "highlight"
    checklist = "checklist"
    objective = "objective"
    playbook_template = "playbook_template"


class EventType(str, Enum):
    new = "new"
    deleted = "deleted"
    status = "status"
    update = "update"


class Status(str, Enum):
    created = "created"
    starting = "starting"
    started = "started"
    completed = "completed"
    queued = "queued"
    scheduled = "scheduled"
    running = "running"
    error = "error"
    skipped = "skipped"
    not_exist = "not_exist"
    submitted = "submitted"
    connected = "connected"
    disconnected = "disconnected"
    restarted = "restarted"
    deleting = "deleting"
    stopping = "stopping"
    exited = "exited"
    downloading = "downloading"
    uploading = "uploading"
    empty = ""

    def __contains__(cls, item):  # type: ignore
        try:
            cls(item)  # type: ignore
        except ValueError:
            return False
        return True


class DomainBase(BaseModel):
    short_name: str | None = None
    long_name: str | None = None


class DomainCreate(DomainBase):
    pass


class Domain(DomainBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    labels: List["Label"] | None = None


class PasswordBase(BaseModel):
    password: str | None = None
    nt: str | None = None
    aes256_key: str | None = None
    aes128_key: str | None = None


class PasswordCreate(PasswordBase):
    pass


class Password(PasswordBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = None


class KerberosBase(BaseModel):
    client: str = ""
    server: str = ""
    key: str = ""
    keytype: str = ""
    auth: datetime | None = None
    start: datetime | None = None
    end: datetime | None = None
    renew: datetime | None = None
    ccache: str = ""
    kirbi: str = ""


class KerberosCreate(KerberosBase):
    pass


class Kerberos(KerberosBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = None


class CredentialBase(BaseModel):
    domain_id: str | UUID4 | None = None
    username: str
    password_id: UUID4 | None = None
    kerberos_id: UUID4 | None = None
    note: str | None = None


class CredentialCreate(CredentialBase):
    mark_owned: bool = True


class Credential(CredentialBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    domain: Domain | None = None
    password: Password | None = None
    kerberos: Kerberos | None = None
    labels: List["Label"] | None = None


class ProxyStatus(str, Enum):
    connected = "connected"
    disconnected = "disconnected"


class ProxyType(str, Enum):
    socks4 = "socks4"
    socks5 = "socks5"


class FileType(str, Enum):
    empty = ""
    lsass = "lsass_dmp"
    nanodump = "nanodump"

    # Text files
    text = "text"
    secretsdump = "secretsdump"

    # Zip files
    zip = "zip"
    bloodhound_zip = "bloodhound_zip"
    harbinger_zip = "harbinger_zip"
    docx = "docx"

    # Json files
    json = "json"
    bloodhound_json = "bloodhound_json"
    pypykatz_json = "pypykatz_json"
    process_list_json = "process_list_json"
    dir2json_json = "dir2json_json"
    certipy_json = "certipy_json"
    certify_json = "certify_json"

    cast = "cast"

    # Exe / dll / bof
    exe = "exe"
    implant_binary = "implant_binary"
    implant_shellcode = "implant_shellcode"
    bof = "bof"

    # Other data formats
    kdbx = "kdbx"
    xml = "xml"
    dir2json = "dir2json"
    ad_snapshot = "ad_snapshot"
    ccache = "ccache"

    yaml = "yaml"

    # harbinger related files
    harbinger_yaml = "harbinger_yaml"
    terminal_recording = "terminal_recording"


class FileTypes(BaseModel):
    types: List[FileType]


class ProxyBase(BaseModel):
    host: str = "localhost"
    port: int = Field(
        gt=0, lt=65536, description="The port must be between 1 and 65,535"
    )
    type: ProxyType
    status: ProxyStatus
    note: str | None = None
    remote_hostname: str | None = None
    username: str | None = ""
    password: str | None = ""
    c2_server_id: str | UUID4 | None = None
    internal_id: str | None = None
    c2_implant_id: str | UUID4 | None = None
    c2_task_id: str | UUID4 | None = None


class ProxyCreate(ProxyBase):
    pass


class Proxy(ProxyBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = None

    def to_str(self) -> str:
        return f"{self.type.name} {self.host} {self.port} {self.username or ''} {self.password or ''}".strip()


class ExecutorTypeName(str, Enum):
    linux = "linux"
    windows = "windows"


class FileBase(BaseModel):
    filetype: FileType | str | None = None
    magic_mimetype: str | None = ""
    magika_mimetype: str | None = ""
    exiftool: str | None = ""
    md5sum: str | None = ""
    sha1sum: str | None = ""
    sha256sum: str | None = ""


class FileUpdate(FileBase):
    pass


class FileCreate(FileBase):
    filename: str
    bucket: str
    path: str
    internal_task_id: str | None = None
    c2_server_id: str | None = None
    internal_implant_id: str | None = None
    manual_timeline_task_id: str | UUID4 | None = None


class File(FileBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    job_id: UUID4 | None
    filename: str
    bucket: str
    path: str
    processing_status: str | None = ""
    processing_progress: int | None = 0
    processing_note: str | None = ""
    c2_task_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    manual_timeline_task_id: str | UUID4 | None = None

    labels: List["Label"] | None = None


class FileContent(BaseModel):
    text: str


class SocksServerType(str, Enum):
    docker = "docker"
    kubernetes = "kubernetes"
    local = "local"


class SocksServerBase(BaseModel):
    type: SocksServerType
    hostname: str
    operating_system: ExecutorTypeName
    status: str | None = ""


class SocksServerCreate(SocksServerBase):
    id: UUID4 | None = None


class SocksServer(SocksServerBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = []


class ProxyJobBase(BaseModel):
    credential_id: UUID4 | str | None = None
    proxy_id: UUID4 | str | None = None
    command: str = ""
    arguments: str = ""
    socks_server_id: UUID4
    playbook_id: UUID4 | str | None = None
    tmate: bool | None = True
    asciinema: bool | None = True
    proxychains: bool | None = True
    env: str | None = ""

    ai_summary: str | None = ""
    processing_status: str | None = ""

    @field_validator('processing_status')
    def set_processing_status(cls, processing_status):
        return processing_status or ''


class ProxyJobCreate(ProxyJobBase):
    input_files: List[str] | None = None


class ProxyJobPreview(ProxyJobBase):
    input_files: List[str] | None = None
    model_config = ConfigDict(from_attributes=True)
    socks_server: SocksServer | None = None


class ProxyJob(ProxyJobBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    status: str | None = "created"
    exit_code: int | None = None
    files: List[File] = []
    time_created: datetime | None = None
    time_updated: datetime | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None
    labels: List["Label"] | None = None
    input_files: List[File] | None = None
    proxy: Proxy | None = None
    credential: Credential | None = None
    socks_server_id: UUID4 | None = None
    socks_server: SocksServer | None = None


class ProxyJobOutputBase(BaseModel):
    job_id: UUID4 | str
    output: str


class ProxyJobOutputCreate(ProxyJobOutputBase):
    pass


class ProxyJobOutput(ProxyJobOutputBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    created_at: datetime | None = None
    output_type: str | None = None


class Component(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    name: str
    hostname: str
    status: str


class ErrorResponse(BaseModel):
    error: str


class UserRead(schemas.BaseUser[uuid.UUID]):
    email: str


class UserCreate(schemas.BaseUserCreate):
    email: str


class UserUpdate(schemas.BaseUserUpdate):
    email: Optional[str] = None


class ProxyChainBase(BaseModel):
    playbook_name: str | None = None
    description: str | None = None
    playbook_template_id: str | UUID4 | None = None


class ProxyChainCreate(ProxyChainBase):
    pass


class ProxyChain(ProxyChainBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    status: str | None = None
    steps: int | None = None
    completed: int | None = None
    arguments: dict | None = None
    time_created: datetime | None = None
    time_updated: datetime | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None
    suggestion_id: UUID4 | None = None

    labels: List["Label"] | None = None


class PlaybookPreview(BaseModel):
    steps: str
    valid: bool
    errors: str = ""
    steps_errors: str | None = ""


class ProxyChainGraph(ProxyChain):
    graph: str = ""
    correct: bool = True


class PlaybookStepModifierBase(BaseModel):
    regex: str | None = None
    input_path: str
    output_path: str
    output_format: str | None = None
    status: str = ""
    on_error: str = ""
    data: str = ""
    status_message: str = ""


class PlaybookStepModifierCreate(PlaybookStepModifierBase):
    playbook_step_id: UUID4 | str


class PlaybookStepModifierEntry(PlaybookStepModifierBase):
    # To pass more data during execution of the workflow
    playbook_step_id: UUID4 | str
    proxy_job_id: UUID4 | str | None = None
    c2_job_id: UUID4 | str | None = None


class PlaybookStepModifier(PlaybookStepModifierBase):
    model_config = ConfigDict(from_attributes=True)
    playbook_step_id: UUID4 | str
    id: UUID4
    time_created: datetime | None = None


class ChainStepBase(BaseModel):
    playbook_id: UUID4 | str | None
    number: int = 0
    label: str | None = ""
    depends_on: str | None = ""
    proxy_job_id: UUID4 | str | None = None
    c2_job_id: UUID4 | str | None = None
    delay: timedelta | None = None
    execute_after: datetime | None = None


class ChainStepCreate(ChainStepBase):
    pass


class ChainStep(ChainStepBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    status: str | None
    time_created: datetime | None = None
    time_updated: datetime | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None
    labels: List["Label"] | None = None
    step_modifiers: List[PlaybookStepModifier] | None = None


class C2JobBase(BaseModel):
    command: str
    arguments: str

    c2_implant_id: UUID4

    playbook_id: UUID4 | str | None = None
    add_labels: list[str] | None = None


class C2JobCreate(C2JobBase):
    input_files: list[str] | None = None


class C2Job(C2JobBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    status: str | None

    message: str | None

    time_created: datetime | None = None
    time_updated: datetime | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None
    labels: List["Label"] | None = None
    input_files: List[File] | None = None


class ProcessBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    process_id: int | None = Field(
        validation_alias=AliasChoices("process_id", "processid", "pid"), default=None
    )
    architecture: str | None = None
    name: str = Field(validation_alias=AliasChoices("name", "process"))
    user: str | None = Field(
        validation_alias=AliasChoices("user", "process"), default=None
    )
    bin_path: str | None = Field(alias="executablepath", default=None)
    parent_process_id: int | None = Field(
        validation_alias=AliasChoices("parent_process_id", "parentprocessid", "ppid"),
        default=None,
    )
    command_line: str | None = Field(alias="commandline", default=None)
    description: str | None = None
    handle: str | None = None
    host_id: str | str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    number: int | None = None

    @field_validator("architecture")
    def validate_architecture(cls, value):
        if not value:
            return ""
        if "64" in value:
            return "x64"
        return "x32"


class ProcessCreate(ProcessBase):
    pass


class Process(ProcessBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = None


class HostBase(BaseModel):
    domain_id: str | UUID4 | None = None
    name: str | None = None
    objectid: str | None = None
    domain: str | None = None
    fqdn: str | None = None


class HostCreate(HostBase):
    pass


class Host(HostBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = None
    domain_obj: Domain | None = None


class Statistics(BaseModel):
    icon: str = ""
    key: str
    value: int | None = None


class StatisticsItems(BaseModel):
    items: list[Statistics]


class ProcessNumbers(BaseModel):
    items: list[int]


class C2Type(str, Enum):
    c2 = "c2"
    proxy = "socks"


class TypeEnum(str, Enum):
    int = "int"
    str = "str"
    bool = "bool"
    options = "options"


class StepArgument(BaseModel):
    name: str
    value: str | int | bool | list[str] = ""


class Step(BaseModel):
    type: C2Type
    name: str
    args: list[StepArgument] | None = None
    delay: int | None = None
    label: str | None = ""
    depends_on: str | None = ""
    tmate: bool | None = True
    asciinema: bool | None = True
    proxychains: bool | None = True
    modifiers: list[PlaybookStepModifierBase] | None = None


class Argument(BaseModel):
    name: str
    type: TypeEnum
    default: str | bool | int | None = None
    description: str = ""
    filetype: str = ""
    required: bool = False
    options: list[str] | None = None


class PlaybookTemplateBase(BaseModel):
    icon: str = ""
    name: str = ""
    tactic: str | None = ""
    technique: str | None = ""
    args: list[Argument] | None = None
    steps: str | None = ""
    yaml: str = ""
    add_depends_on: bool | None = None


class PlaybookTemplateGenerated(BaseModel):
    icon: str 
    name: str
    tactic: str
    technique: str
    args: list[Argument]
    steps: str
    add_depends_on: bool


class PlaybookTemplateView(PlaybookTemplateBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 = Field(default_factory=uuid4)
    labels: List["Label"] | None = []


class PlaybookTemplateCreate(PlaybookTemplateBase):
    labels: list[str] | None = []
    id: UUID4 = Field(default_factory=uuid4)


class PlaybookTemplate(PlaybookTemplateCreate):
    model_config = ConfigDict(from_attributes=True)
    add_depends_on: bool | None = True

    def create_fields(self, default_arguments: dict | None = None) -> dict:
        result = {}
        for arg in self.args or []:
            default = arg.default
            options = arg.options or []
            if arg.required:
                default = ...  # type: ignore
            if default_arguments and arg.name in default_arguments:
                if (
                    type(default_arguments[arg.name]) == list
                    and default_arguments[arg.name]
                ):
                    options = default_arguments[arg.name]
                    arg.type = TypeEnum.options
                    default = options[0]
                else:
                    default = default_arguments[arg.name]
            if arg.type == TypeEnum.options:
                arg_type = Literal[tuple(options)]  # type: ignore
            else:
                arg_type = getattr(builtins, arg.type)
            result[arg.name] = (
                arg_type,
                Field(
                    default=default,
                    description=arg.description,
                    filetype=arg.filetype,  # type: ignore
                ),
            )
        return result

    def create_model(self, default_arguments: dict | None = None):
        return create_model(
            self.name,
            **self.create_fields(default_arguments),
        )


def create_random_color():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return "#{:02x}{:02x}{:02x}".format(int(r), int(g), int(b))


class LabelBase(BaseModel):
    name: str
    category: str
    color: str | None = ''

    model_config = ConfigDict(validate_default=True)

    @field_validator("color")
    def validate_color(cls, value):
        if not value:
            return create_random_color()
        return value


class LabelCreate(LabelBase):
    id: str | UUID4 | None = None


class Label(LabelBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4


class LabelView(BaseModel):
    category: str
    labels: list[Label]


class LabeledItemBase(BaseModel):
    label_id: UUID4 | str
    domain_id: str | UUID4 | None = None
    password_id: str | UUID4 | None = None
    credential_id: str | UUID4 | None = None
    kerberos_id: str | UUID4 | None = None
    proxy_id: str | UUID4 | None = None
    proxy_job_id: str | UUID4 | None = None
    proxy_job_output: str | UUID4 | None = None
    file_id: str | UUID4 | None = None
    playbook_id: str | UUID4 | None = None
    playbook_step_id: str | UUID4 | None = None
    c2_job_id: str | UUID4 | None = None
    host_id: str | UUID4 | None = None
    process_id: str | UUID4 | None = None
    playbook_template_id: str | UUID4 | None = None
    c2_server_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    c2_task_id: str | UUID4 | None = None
    c2_task_output_id: str | UUID4 | None = None
    share_id: str | UUID4 | None = None
    share_file_id: str | UUID4 | None = None
    hash_id: str | UUID4 | None = None
    highlight_id: str | UUID4 | None = None
    parse_result_id: str | UUID4 | None = None
    socks_server_id: str | UUID4 | None = None
    action_id: str | UUID4 | None = None
    certificate_template_id: str | UUID4 | None = None
    certificate_authority_id: str | UUID4 | None = None
    manual_timeline_task_id: str | UUID4 | None = None
    suggestion_id: str | UUID4 | None = None
    plan_id: str | UUID4 | None = None
    plan_step_id: str | UUID4 | None = None


class LabeledItemCreate(LabeledItemBase):
    pass


class LabeledItemDelete(LabeledItemBase):
    label_id: UUID4 | str | None = None  # type: ignore


class LabeledItem(LabeledItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime | None = None
    label: Label | None = None


class FileConfig(BaseModel):
    id: UUID4
    path: str
    name: str
    type: FileType


class ArgumentNameEnum(str, Enum):
    hostname = 'hostname'
    username = 'username'
    password = 'password'
    ca_certificate = 'ca_certificate'
    certificate = 'certificate'
    private_key = 'private_key'
    token = 'token'
    port = 'port'


class RequiredArgument(BaseModel):
    name: ArgumentNameEnum
    regex: str | None = ''
    default: str | int | None = None
    error: str | None = 'Please fill in this value'
    type: str | None = None

    def default_type(self) -> str | None:
        match self.name:
            case ArgumentNameEnum.ca_certificate | ArgumentNameEnum.certificate | ArgumentNameEnum.private_key:
                return "textarea"
            case ArgumentNameEnum.port:
                return "number"
            case ArgumentNameEnum.hostname | ArgumentNameEnum.username | ArgumentNameEnum.password | ArgumentNameEnum.token:
                return "text"
            case _:
                return None


class Implant(BaseModel):
    name: str
    icon_base64: str | None = ''
    commands: List[str]


class C2ServerTypeYaml(BaseModel):
    id: UUID4
    name: str
    docker_image: str
    command: str
    icon_base64: str | None = ''
    required_arguments: List[RequiredArgument]
    implants: List[Implant] = []


class C2ServerTypeBase(BaseModel):
    time_created: datetime | None = None
    time_updated: datetime | None = None
    name: str | None = None
    docker_image: str | None = None
    command: str | None = None


class C2ServerTypeCreate(C2ServerTypeBase):
    id: UUID4 | str | None = None
    icon: str | None = None


class C2ServerType(C2ServerTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

    arguments: list['C2ServerArguments'] | None = None


class HarbingerYaml(BaseModel):
    files: List[FileConfig] | None = None
    c2_server_types: List[C2ServerTypeYaml] | None = None
    labels: List[LabelCreate] | None = None
    actions: List["ActionCreate"] | None = None
    setting_categories: List["SettingCategoryCreate"] | None = None
    playbooks: List["PlaybookTemplateCreate"] | None = None
    c2_servers: List["C2ServerCreate"] | None = None


class C2ServerArgumentsBase(BaseModel):
    time_created: datetime | None = None
    name: str | None = None
    regex: str | None = None
    default: str | None = None
    error: str | None = None
    type: str | None = None
    c2_server_type_id: str | UUID4 | None = None
    

class C2ServerArgumentsCreate(C2ServerArgumentsBase):
    pass


class C2ServerArgumentsCreated(C2ServerArgumentsBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class C2ServerArguments(C2ServerArgumentsBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class ProcessMapping(BaseModel):
    name: str
    description: str
    type: str
    tag_id: str
    processes: List[str]


class StatusResponse(BaseModel):
    message: str = ""


class TimeLineThemes(str, Enum):
    asciinema = "asciinema"
    dracula = "dracula"
    github_dark = "github_dark"
    github_light = "github-light"
    monokai = "monokai"
    nord = "nord"
    solarized_dark = "solarized-dark"
    solarized_light = "solarized-light"


class CreateTimeline(BaseModel):
    create_screenshots: bool = True
    theme: TimeLineThemes = TimeLineThemes.asciinema
    hour_offset: int = 0


class C2ServerStatus(BaseModel):
    status: str = ""
    message: str = ""
    name: str = ""


class C2ServerStatusUpdate(BaseModel):
    status: C2ServerStatus
    c2_server_id: str


class C2ServerBase(BaseModel):
    type: str | None = None
    name: str | None = ""
    hostname: str | None = ""
    username: str | None = ""
    port: int | None = None


class C2ServerCreate(C2ServerBase):
    password: str | None = ""
    ca_certificate: str | None = ""
    certificate: str | None = ""
    private_key: str | None = ""
    token: str | None = ""


class C2Server(C2ServerBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = []
    status: List[C2ServerStatus] | None = []


class C2ServerAll(C2ServerBase):
    model_config = ConfigDict(from_attributes=True)
    password: str | None = ""
    ca_certificate: str | None = ""
    certificate: str | None = ""
    private_key: str | None = ""
    token: str | None = ""


class C2ImplantBase(BaseModel):
    c2_server_id: UUID4 | str
    internal_id: str | None = Field(
        validation_alias=AliasChoices("c2_uid", "ID", "internal_id"), default=None
    )
    c2_type: str | None = None
    payload_type: str | None = None
    name: str | None = Field(
        validation_alias=AliasChoices("name", "Name"), default=None
    )
    hostname: str = Field(
        validation_alias=AliasChoices("computer", "hostname", "host", "Hostname"),
        default="",
    )
    description: str | None = Field(
        validation_alias=AliasChoices("description", "note"), default=""
    )
    sleep: int | None = None
    jitter: int | None = None
    os: str | None = Field(validation_alias=AliasChoices("os", "OS"), default=None)
    pid: int | None = Field(validation_alias=AliasChoices("pid", "PID"), default=None)
    architecture: str | None = Field(
        validation_alias=AliasChoices("architecture", "barch", "Arch", "bitness"),
        default="",
    )
    process: str | None = Field(
        validation_alias=AliasChoices("process", "process_name", "Filename"), default=""
    )
    username: str = Field(
        validation_alias=AliasChoices("username", "user", "Username"), default=""
    )
    ip: str | None = Field(validation_alias=AliasChoices("ip", "host"), default="")
    external_ip: str | None = Field(
        validation_alias=AliasChoices("external", "external_ip", "RemoteAddress"),
        default="",
    )
    domain: str | None = None
    last_checkin: datetime | None = Field(
        validation_alias=AliasChoices("last_checkin", "LastCheckin", "last_heartbeat"),
        default=None,
    )
    host_id: UUID4 | str | None = None

    @field_validator("architecture")
    def validate_architecture(cls, value):
        if not value:
            return ""
        if "64" in value:
            return "x64"
        return "x32"

    @field_validator("os")
    def validate_os(cls, value):
        if not value:
            return ""
        if "windows" in value.lower():
            return "windows"
        if "linux" in value.lower():
            return "linux"
        return value


class C2ImplantCreate(C2ImplantBase):
    internal_id: str | None = Field(
        validation_alias=AliasChoices("c2_uid", "ID", "internal_id"), default=None
    )


class C2ImplantUpdate(C2ImplantCreate):
    c2_server_id: UUID4 | str | None = None


class C2Implant(C2ImplantBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = []


class C2TaskBase(BaseModel):
    internal_id: str | None = None
    c2_implant_id: UUID4 | str | None = None
    c2_server_id: UUID4 | str | None = None
    status: str | None = None
    original_params: str | None = None
    display_params: str | None = None
    time_started: datetime | None = Field(
        validation_alias=AliasChoices(
            "status_timestamp_processing", "started_at", "time_started"
        ),
        default=None,
    )
    time_completed: datetime | None = Field(
        validation_alias=AliasChoices("timestamp", "finished_at", "time_completed"),
        default=None,
    )
    command_name: str | None = Field(
        validation_alias=AliasChoices("command_name", "command"), default=""
    )
    operator: str | None = Field(
        validation_alias=AliasChoices("operator", "user", "created_by"), default=""
    )
    ai_summary: str | None = ""
    processing_status: str | None = ""

    @field_validator('processing_status')
    def set_processing_status(cls, processing_status):
        return processing_status or ''

class C2TaskCreate(C2TaskBase):
    internal_implant_id: str


class C2Task(C2TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    labels: List["Label"] | None = []


class C2OutputBase(BaseModel):
    internal_id: str | None = None
    c2_implant_id: UUID4 | str | None = None
    c2_task_id: UUID4 | str | None = None
    c2_server_id: UUID4 | str
    response_text: str | None = Field(
        validation_alias=AliasChoices("response_text", "result"), default=""
    )
    output_type: str | None = Field(
        validation_alias=AliasChoices("output_type", "type"), default=""
    )
    timestamp: datetime | None = None

    @field_validator("response_text")
    @classmethod
    def remove_nullbytes(cls, v: str) -> str:
        if v:
            return v.replace("\x00", "")
        return v


class FileList(BaseModel):
    host: str
    parent_path: str
    name: str
    domain: str = ''

    unc_path: str = ''
    sharename: str = ''
    share_unc_path: str = ''
    depth: int = 0

    size: int = 0
    last_accessed: datetime | None = None
    last_modified: datetime | None = None
    files: List["ShareFileCreate"] | None = None

    parents: List["ShareFileCreate"] | None = None


    def to_base_parsed_share_file(self) -> 'BaseParsedShareFile':
        result = BaseParsedShareFile(
            name=self.name,
            domain=self.domain,
            unc_path=self.unc_path,
            share_unc_path=self.share_unc_path,
            depth=self.depth,
            size=self.size,
            type="dir",
            indexed=True,
            parents=[],
            children=[],
            sharename=self.sharename,
            hostname=self.host,
        )

        for parent in self.parents or []:
            result.parents.append(
                BaseParsedShareFile(
                    name=parent.name,
                    size=parent.size or 0,
                    type="dir",
                    unc_path=parent.unc_path or '',
                    depth=parent.depth or 0,
                )
            )
        
        for file in self.files or []:
            result.children.append(
                BaseParsedShareFile(
                    name=file.name,
                    size=file.size or 0,
                    type=file.type or '',
                    unc_path=file.unc_path or '',
                    depth=file.depth or 0,
                )
            )
        return result

    # Modify the filenames from for example C:\ to \\hostname.domain\C$
    # Raised ValueError if the sharename doesn't start with \\ and the hostname is not defined.
    def parse(self, indexer: bool = True):
        if not self.name.startswith("\\"):
            # print("not self.name.startswith('\\')")
            if not self.host:
                raise ValueError("Cannot parse the file without hostname")
            share = ""
            if self.parent_path:
                if self.parent_path.startswith("\\"):
                    hostpart = [x for x in self.parent_path.split("\\") if x]
                    if len(hostpart) > 1:
                        share = hostpart[1]
                        self.host = hostpart[0]
                        self.name = ntpath.join(*hostpart[1:], self.name)
                    else:
                        share = self.name
                        self.host = hostpart[0]
                else:
                    share = self.parent_path.split("\\")[0]
                    self.name = f"{self.parent_path}\\{self.name}"
            elif "\\" in self.name:
                share = self.name.split("\\")[0]
            self.sharename = share.replace(":", "$")
            self.share_unc_path = f"\\\\{self.host}\\{self.sharename}"
            self.name = self.name.replace(share, self.share_unc_path)
            if "." in self.host:
                self.host, self.domain = self.host.split('.', 1)
        else:
            hostpart = [x for x in self.name.split("\\") if x]
            if "." in hostpart[0]:
                self.host, self.domain = hostpart[0].split(".", 1)
            else:
                self.host = hostpart[0]
            self.share_unc_path = f"\\\\{ntpath.join(*hostpart[0:2])}"
            self.sharename = hostpart[1]

        split = [n for n in self.name.split("\\") if n][2:]
        parts = split[:-1]

        self.name = ""
        depth = 0
        self.parents = []

        if split:
            self.name = split[-1]
            self.parents.append(
                ShareFileCreate(
                    name="",
                    type="dir",
                    unc_path=self.share_unc_path,
                    indexed=len(parts) == 0 and indexer,
                    depth=0,
                )
            )
            depth += 1

        for part in parts:
            self.parents.append(
                ShareFileCreate(
                    name=part,
                    type="dir",
                    unc_path=ntpath.join(self.share_unc_path, *parts[0:depth]),
                    depth=depth,
                    indexed=False,
                )
            )
            depth += 1

        self.depth = depth
        self.unc_path = ntpath.join(self.share_unc_path, *split)
        for file in self.files or []:
            file.fix_fields(self.unc_path, self.depth)


class C2OutputCreate(C2OutputBase):
    response_bytes: bytes | str | None = None
    internal_task_id: str

    bucket: str | None = None
    path: str | None = None

    processes: List[ProcessCreate] | None = []
    file_list: FileList | None = None

    @field_validator("response_bytes")
    @classmethod
    def fix_response_bytes(cls, v: bytes | str | None) -> bytes | None:
        if isinstance(v, str):
            return v.encode("utf-8")
        return v


class C2OutputCreated(BaseModel):
    created: bool = False
    output: str
    c2_output_id: UUID4 | str
    c2_implant_id: UUID4 | str | None
    highest_process_number: int = 0
    host_id: UUID4 | str | None = None


class C2Output(C2OutputBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    labels: List["Label"] | None = []


class C2OutputPlaybook(BaseModel):
    task: C2TaskBase
    output: list[C2OutputCreate]


class TimeLine(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    status: str | None = ""
    command_name: str | None = Field(
        validation_alias=AliasChoices("command_name", "command"), default=""
    )
    arguments: str | None = Field(
        validation_alias=AliasChoices("arguments", "display_params"), default=""
    )
    original_params: str | list | None = ""
    argument_params: str | list | None = ""
    operator: str | None = ""
    time_started: datetime | None = None
    time_completed: datetime | None = None
    hostname: str | None = ""
    object_type: str | None = ""
    output: str | None = ""
    ai_summary: str | None = ""
    processing_status: str | None = ""

    @field_validator('processing_status')
    def set_processing_status(cls, processing_status):
        return processing_status or ''

    @model_validator(mode="before")  # type: ignore
    @classmethod
    def validate_hostname(cls, data: Any) -> Any:
        data.object_type = data.__class__.__name__
        if hasattr(data, "c2_implant") and data.c2_implant:
            data.hostname = data.c2_implant.hostname
        if hasattr(data, "proxy"):
            if data.proxy:
                data.hostname = data.proxy.remote_hostname
        if hasattr(data, "original_params"):
            if data.original_params and "arguments" in data.original_params:
                try:
                    data.argument_params = json.loads(data.original_params).get(
                        "arguments", ""
                    )
                except json.decoder.JSONDecodeError:
                    pass
        return data


class SituationalAwarenessBase(BaseModel):
    name: str
    category: str
    value_string: str | None = None
    value_int: int | None = None
    value_bool: bool | None = None
    value_json: dict | None = None
    domain_id: str | UUID4 | None = None


class SituationalAwarenessCreate(SituationalAwarenessBase):
    @model_validator(mode="after")  # type: ignore
    def check_value_set(self) -> "SituationalAwarenessCreate":
        if not any(
            [self.value_string, self.value_bool, self.value_int is not None, self.value_json]
        ):
            raise ValueError("At least one value must be set")
        return self


class SACategories(str, Enum):
    domain = "Domain"
    host = "Host"


class SANames(str, Enum):
    dns_server = "DNS Server"
    dns_server_ip = "DNS Server IP"
    domain_controller = "Domain Controller"
    domain_controller_ip = "Domain Controller IP"
    machine_account_quota = "Machine Account Quota"


class SituationalAwareness(SituationalAwarenessBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime
    domain: Domain | None = None


class ShareBase(BaseModel):
    host_id: str | UUID4 | None = None
    name: str | None = ""
    unc_path: str
    type: int | None = None
    remark: str | None = ""

    @field_validator("name", "unc_path", "remark")
    @classmethod
    def clean(cls, v: str) -> str:
        try:
            return v.replace("\x00", "")
        except AttributeError:
            return v

    @field_validator("name", "unc_path")
    @classmethod
    def upper_case(cls, v: str) -> str:
        try:
            return v.upper()
        except AttributeError:
            return v


class ShareCreate(ShareBase):
    pass


class Share(ShareBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime

    labels: List["Label"] | None = None


class ShareFileBase(BaseModel):
    type: str | None = ""
    file_id: str | UUID4 | None = None
    parent_id: str | UUID4 | None = None
    share_id: str | UUID4 | None = None
    size: int | None = None
    last_accessed: datetime | None = None
    last_modified: datetime | None = None
    created: datetime | None = None
    unc_path: str | None = None
    depth: int | None = None
    extension: str | None = None
    name: str
    downloaded: bool = False
    indexed: bool = False


class ShareFileCreate(ShareFileBase):

    @model_validator(mode="after")  # type: ignore
    def set_extension(self) -> "ShareFileCreate":
        if "." in self.name:
            self.extension = self.name.split(".")[-1].lower()
        return self

    def fix_fields(self, parent_unc_path: str, depth: int) -> None:
        if not self.unc_path:
            self.unc_path = ntpath.join(parent_unc_path, self.name)
        if not self.depth:
            self.depth = depth


class ShareFile(ShareFileBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime

    labels: List["Label"] | None = None


class BaseParsedShareFile(BaseModel):
    attributes: int = 0
    name: str
    size: int = 0
    timestamp: None | int | datetime = None
    children: list["BaseParsedShareFile"] = []
    type: str = ""
    unc_path: str = ""
    sharename: str = ""
    share_unc_path: str = ""
    depth: int = 0
    hostname: str = ""
    domain: str = ""
    indexed: bool = False
    parents: list["BaseParsedShareFile"] = []

    def count(self) -> int:
        count = len(self.children)
        for child in self.children:
            count += child.count()
        return count

    # Modify the filenames from for example C:\ to \\hostname.domain\C$
    # Raised ValueError if the sharename doesn't start with \\ and the hostname is not defined.
    def parse(self, hostname: str, domain: str, indexer: bool = True):
        self.parents = []
        if not self.name.startswith("\\"):
            if not hostname:
                raise ValueError("Cannot parse the file without hostname")
            host = hostname
            if domain:
                host = f"{host}.{domain}"
            share = self.name.split("\\")[0]
            self.sharename = share.replace(":", "$")
            self.share_unc_path = f"\\\\{host}\\{self.sharename}"
            self.hostname = hostname
            self.domain = domain
            self.name = self.name.replace(share, self.share_unc_path)
        else:
            hostpart = [x for x in self.name.split("\\") if x]
            if "." in hostpart[0]:
                self.hostname, self.domain = hostpart[0].split(".", 1)
            else:
                self.hostname = hostpart[0]
            self.share_unc_path = f"\\\\{ntpath.join(*hostpart[0:2])}"
            self.sharename = hostpart[1]

        split = [n for n in self.name.split("\\") if n][2:]
        parts = split[:-1]

        self.name = ""
        depth = 0

        if split:
            self.name = split[-1]
            self.parents.append(
                BaseParsedShareFile(
                    name="",
                    type="dir",
                    unc_path=self.share_unc_path,
                    indexed=len(parts) == 0 and indexer,
                    depth=0,
                )
            )
            depth += 1

        for part in parts:
            self.parents.append(
                BaseParsedShareFile(
                    name=part,
                    type="dir",
                    unc_path=ntpath.join(self.share_unc_path, *parts[0:depth]),
                    depth=depth,
                    indexed=False,
                )
            )
            depth += 1

        self.depth = depth
        self.unc_path = ntpath.join(self.share_unc_path, *split)


class Dir2JsonShareFile(BaseParsedShareFile):
    attributes: int = Field(alias="A", default=0)
    name: str = Field(alias="N")
    size: int = Field(alias="S", default=0)
    timestamp: None | int | datetime = Field(alias="T", default=None)
    children: list["Dir2JsonShareFile"] = Field(alias="C", default=[])

    @field_validator("timestamp")
    @classmethod
    def parse_timestamp(cls, v: int) -> datetime:
        return datetime(1601, 1, 1) + timedelta(microseconds=v / 10)

    @model_validator(mode="after")  # type: ignore
    def set_type(self) -> "Dir2JsonShareFile":
        if not self.type:
            self.type = "dir" if self.attributes & 0x10 else "file"
        return self


class MythicShareFile(BaseParsedShareFile):
    host: str = ""
    is_file: bool = Field(exclude=True)
    access_time: datetime
    creation_time: datetime
    modify_time: datetime
    name: str
    parent_path: str = ""
    children: list["MythicShareFile"] = Field(alias="files", default=[])

    @model_validator(mode="after")  # type: ignore
    def set_type(self) -> "MythicShareFile":
        if not self.type:
            self.type = "file" if self.is_file else "dir"
        return self

    @model_validator(mode="after")  # type: ignore
    def set_name(self) -> "MythicShareFile":
        if self.parent_path:
            self.name = ntpath.join(self.parent_path, self.name)
        return self


class CobaltstrikeShareFile(BaseParsedShareFile):
    modify_time: str | None | datetime = None
    size: int = 0
    name: str
    children: list["BaseParsedShareFile"] = []

    @model_validator(mode="after")  # type: ignore
    def set_type(self) -> "CobaltstrikeShareFile":
        if self.type in ["D", "F"]:
            self.type = "dir" if self.type == "D" else "file"
        return self


class Command(str, Enum):
    start = "start"
    stop = "stop"
    restart = "restart"
    create = "create"
    delete = "delete"
    sync = "sync"


class C2ServerCommand(BaseModel):
    name: str = ""
    command: Command
    id: str | UUID4 | None = None
    c2_server: C2Server | None = None


class HashBase(BaseModel):
    hash: str
    type: str
    hashcat_id: int = 0

    @field_validator("hash")
    @classmethod
    def remove_nullbytes(cls, v: str) -> str:
        return v.replace("\x00", "")


class HashCreate(HashBase):
    pass


class Hash(HashBase):
    id: UUID4
    time_created: datetime
    status: str | None = ""
    labels: List["Label"] | None = []


class LabelProcess(BaseModel):
    host_id: str
    number: int


class TextParse(BaseModel):
    text: str
    c2_implant_id: str | UUID4 | None = None
    c2_output_id: str | UUID4 | None = None


class WorkflowStepResult(BaseModel):
    id: str | UUID4
    status: str
    proxy_id: str | UUID4 | None = None
    output: str = ""
    label: str = ""


# Trufflehog output schemas.
class THEntry(BaseModel):
    file: str
    line: int


class THData(BaseModel):
    filesytem: THEntry = Field(validation_alias="Filesystem")


class THSourceMetadata(BaseModel):
    data: THData = Field(validation_alias="Data")


class TruffleHogOutput(BaseModel):
    source_meta_data: THSourceMetadata | None = Field(
        validation_alias="SourceMetadata", default=None
    )
    source_id: int | None = Field(validation_alias="SourceID", default=None)
    source_type: int | None = Field(validation_alias="SourceType", default=None)
    source_name: str | None = Field(validation_alias="SourceName", default=None)
    detector_type: int | None = Field(validation_alias="DetectorType", default=None)
    detector_name: str | None = Field(validation_alias="DecoderName", default=None)
    raw: str | None = Field(validation_alias="Raw", default=None)
    raw_v2: str | None = Field(validation_alias="RawV2", default=None)
    extra_data: dict | None = Field(validation_alias="ExtraData", default=None)
    structured_data: str | None = Field(validation_alias="StructuredData", default=None)


class NPBlobMetadata(BaseModel):
    charset: str | None = ""
    id: str | None = ""
    mime_essence: str | None = ""
    num_bytes: int | None = 0


class NPSnippet(BaseModel):
    after: str | None = ""
    before: str | None = ""
    matching: str | None = ""


class NPOffset(BaseModel):
    column: int
    line: int


class NPSpan(BaseModel):
    start: NPOffset
    end: NPOffset


class NPLocation(BaseModel):
    source_span: NPSpan


class NPMatch(BaseModel):
    blob_id: str | None = ""
    blob_metadata: NPBlobMetadata
    comment: str | None = ""
    groups: list[str] | None = None
    location: NPLocation
    rule_name: str | None = ""
    rule_structural_id: str | None = ""
    rule_text_id: str | None = ""
    score: str | None = ""
    snippet: NPSnippet
    status: str | None = ""
    structural_id: str | None = ""


class NoseyParkerOutput(BaseModel):
    finding_id: str | None = ""
    groups: list[str] | None = None
    matches: list[NPMatch]
    mean_score: int | None = None
    num_matches: int | None = 0
    rule_name: str | None = ""
    rule_structural_id: str | None = ""
    rule_text_id: str | None = ""
    commend: str | None = ""


class HighlightBase(BaseModel):
    file_id: UUID4 | str | None = None
    c2_task_id: UUID4 | str | None = None
    c2_task_output_id: UUID4 | str | None = None
    proxy_job_output_id: UUID4 | str | None = None
    parse_result_id: UUID4 | str | None = None
    proxy_job_id: UUID4 | str | None = None
    rule_id: int | None = None
    rule_type: str | None = None
    hit: str | None = None
    start: int | None = None
    end: int | None = None
    line: int | None = None


class HighlightCreate(HighlightBase):
    pass


class Highlight(HighlightBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime
    labels: List["Label"] | None = []


class ParseResultBase(BaseModel):
    file_id: UUID4 | str | None = None
    c2_task_id: UUID4 | str | None = None
    c2_task_output_id: UUID4 | str | None = None
    proxy_job_output_id: UUID4 | str | None = None
    proxy_job_id: UUID4 | str | None = None
    parser: str | None = None
    log: str | None = None


class ParseResultCreate(ParseResultBase):
    pass


class ParseResult(ParseResultBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime
    labels: List["Label"] | None = []


class FilterOption(BaseModel):
    name: str | None = ""
    count: int = 0
    color: str | None = ""


class Filter(BaseModel):
    name: str
    icon: str
    type: str
    multiple: bool = False
    query_name: str
    options: list[FilterOption] = []


class SettingBase(BaseModel):
    name: str
    type: str
    description: str
    category_id: UUID4
    value: Any


class SettingModify(BaseModel):
    value: Any


class SettingCreate(SettingBase):
    category_id: UUID4 | None | str = ""


class Setting(SettingBase):
    id: UUID4
    model_config = ConfigDict(from_attributes=True)


class SettingCategoryBase(BaseModel):
    name: str
    description: str
    icon: str
    order: int


class SettingCategoryCreate(SettingCategoryBase):
    settings: list[SettingCreate]


class SettingCategory(SettingCategoryBase):
    id: UUID4
    model_config = ConfigDict(from_attributes=True)


class Settings(SettingCategoryBase):
    settings: list[Setting]


class RunJob(BaseModel):
    c2_job: C2Job
    c2_implant: C2Implant


class WaitForTask(BaseModel):
    c2_task: C2Task
    c2_implant: C2Implant


class C2Connector(BaseModel):
    c2_server_id: str
    name: str


class C2TaskStatus(BaseModel):
    c2_task_id: str | UUID4
    status: str
    message: str | None = ""


class C2JobTaskMapping(BaseModel):
    c2_job_id: str | UUID4
    c2_task_id: str | UUID4


class ActionBase(BaseModel):
    name: str
    description: str | None = ""
    status: str | None = ""


class ActionCreate(ActionBase):
    id: UUID4 | str
    labels: List[str] = Field(default=[], exclude=True)
    playbook_template_ids: List[UUID4] = Field(default=[], exclude=True)


class Action(ActionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    time_created: datetime | None = None
    time_updated: datetime | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None

    labels: List["Label"] | None = None
    playbook_templates: List["PlaybookTemplateView"] | None = None


class CertificateTemplatePermissionBase(BaseModel):
    certificate_template_id: str | UUID4 | None = None
    permission: str | None = None
    principal: str | None = None
    principal_type: str | None = None
    object_id: str | None = None


class CertificateTemplatePermissionCreate(CertificateTemplatePermissionBase):
    pass


class CertificateTemplatePermission(CertificateTemplatePermissionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    time_created: datetime | None = None
    time_updated: datetime | None = None


class CertificateTemplateBase(BaseModel):
    template_name: str | None = None
    display_name: str | None = None
    enabled: bool | None = None
    client_authentication: bool | None = None
    enrollment_agent: bool | None = None
    any_purpose: bool | None = None
    enrollee_supplies_subject: bool | None = None
    requires_manager_approval: bool | None = None
    requires_manager_archival: bool | None = None
    authorized_signatures_required: int | None = None
    validity_period: str | None = None
    renewal_period: str | None = None
    minimum_rsa_key_length: int | None = None


class CertificateTemplateCreate(CertificateTemplateBase):
    certificate_authorities: list[str] | None = []


class CertificateTemplate(CertificateTemplateBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    time_created: datetime | None = None
    time_updated: datetime | None = None

    labels: List["Label"] | None = None


class CertificateAuthorityBase(BaseModel):
    ca_name: str | None = None
    dns_name: str | None = None
    certificate_subject: str | None = None
    certificate_serial_number: str | None = None
    certificate_validity_start: str | None = None
    certificate_validity_end: str | None = None
    web_enrollment: str | None = None
    user_specified_san: str | None = None
    request_disposition: str | None = None
    enforce_encryption_for_requests: str | None = None


class CertificateAuthorityCreate(CertificateAuthorityBase):
    pass


class CertificateAuthority(CertificateAuthorityBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    time_created: datetime | None = None
    time_updated: datetime | None = None

    labels: List["Label"] | None = None


class IssueBase(BaseModel):
    name: str | None = None
    description: str | None = None
    impact: str | None = None
    exploitability: str | None = None
    label_id: str | UUID4 | None = None


class IssueCreate(IssueBase):
    pass


class IssueCreated(IssueBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class Issue(IssueBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    time_created: datetime | None = None
    time_updated: datetime | None = None

    labels: List["Label"] | None = None


# --- Graph Schemas ---

class GraphBase(BaseModel):
    name: str
    description: str | None = None


class GraphCreate(GraphBase):
    pass


class Graph(GraphBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

    labels: List["Label"] | None = None


class GraphNodeBase(BaseModel):
    node_type: str
    attributes: dict | str
    source: str | None = None
    graph_id: UUID4 | str


class GraphNodeCreate(GraphNodeBase):
    pass


class GraphNode(GraphNodeBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime
    time_updated: datetime | None = None


class GraphEdgeBase(BaseModel):
    source_id: UUID4 | str
    target_id: UUID4 | str
    verb: str
    source: str | None = None
    graph_id: UUID4 | str


class GraphEdgeCreate(GraphEdgeBase):
    pass


class GraphEdge(GraphEdgeBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4
    time_created: datetime
    time_updated: datetime | None = None


class ManualTimelineTaskBase(BaseModel):
    time_created: datetime | None = None
    status: str | None = None
    arguments: str | None = None
    time_started: datetime | None = None
    time_completed: datetime | None = None
    command_name: str | None = None
    operator: str | None = None
    output: str | None = None
    hostname: str | None = None
    ai_summary: str | None = ""
    processing_status: str | None = ""

    @field_validator('processing_status')
    def set_processing_status(cls, processing_status):
        return processing_status or ''


class ManualTimelineTaskCreate(ManualTimelineTaskBase):
    pass


class ManualTimelineTaskCreated(ManualTimelineTaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class ManualTimelineTask(ManualTimelineTaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

    labels: List["Label"] | None = None


class ProgressBar(BaseModel):
    current: int = 0
    max: int = 100
    percentage: float = 0.0
    type: str = ""
    id: str = ""
    description: str = ""

    model_config = ConfigDict(validate_default=True)

    @model_validator(mode='after')
    def validate_percentage(self) -> Self:
        self.percentage = self.current / self.max
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    def increase(self, step: int = 0):
        self.current += step
        self.percentage = self.current / self.max


class SuggestionBase(BaseModel):
    name: str | None = None
    reason: str | None = None
    playbook_template_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    arguments: dict | None = None
    command: str | None = None
    plan_step_id: UUID4 | str | None = None


class SuggestionCreate(SuggestionBase):
    pass


class SuggestionCreated(SuggestionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class Suggestion(SuggestionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str
    time_created: datetime | None = None
    time_updated: datetime | None = None

    labels: List["Label"] | None = None


class SuggestionBaseRequest(BaseModel):
    credentials: bool = True
    playbooks: bool = True
    c2_tasks: bool = True
    c2_task_output: bool = True
    proxies: bool = True

class C2ImplantSuggestionRequest(SuggestionBaseRequest):
    c2_implant_id: str
    additional_prompt: str = ''


class SuggestionsRequest(SuggestionBaseRequest):
    additional_prompt: str = ''


class C2JobDetectionRiskRequest(SuggestionBaseRequest):
    additional_prompt: str = ''
    c2_job_id: UUID4 | str


class PlaybookDetectionRiskSuggestion(SuggestionBaseRequest):
    additional_prompt: str = ''
    playbook_id: str


class ChecklistBase(BaseModel):
    domain_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    phase: str | None = None
    name: str | None = None
    status: str | None = None
    

class ChecklistCreate(ChecklistBase):
    pass


class ChecklistCreated(ChecklistBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class Checklist(ChecklistBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

    labels: List["Label"] | None = None


class ObjectiveBase(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    time_created: datetime | None = None
    time_updated: datetime | None = None
    

class ObjectiveCreate(ObjectiveBase):
    pass


class ObjectiveCreated(ObjectiveBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class Objective(ObjectiveBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str

    labels: List["Label"] | None = None


class ReadmeInput(BaseModel):
    """Schema for receiving README content."""
    readme: str = Field(..., description="The README content in markdown format.")


class GeneratedYamlOutput(BaseModel):
    """Schema for returning the AI-generated YAML."""
    yaml: str = Field(..., description="The generated playbook template YAML string.")


class PlanStepBase(BaseModel):
    description: str = ''
    order: int = 0
    notes: Optional[str] = None
    status: str | None = ''
    llm_status: str | None = ''
    plan_id: str | UUID4 | None = None


class PlanStepCreate(PlanStepBase):
    pass


class PlanStepUpdate(PlanStepBase):
    pass


class PlanStep(PlanStepBase):
    id: UUID4
    suggestions: List["Suggestion"] = []
    time_created: datetime | None = None
    time_updated: datetime | None = None
    labels: List["Label"] = []
    model_config = ConfigDict(from_attributes=True)


class PlanBase(BaseModel):
    name: str
    objective: str | None = None
    status: str | None = ''
    llm_status: str | None = ''


class PlanCreate(PlanBase):
    pass


class PlanUpdate(PlanBase):
    name: str | None = None


class PlanCreated(ChecklistBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class Plan(PlanBase):
    id: UUID4
    time_created: datetime | None = None
    time_updated: datetime | None = None
    # steps: List[PlanStep] = []
    labels: List["Label"] = []
    model_config = ConfigDict(from_attributes=True)


# Using Enum for validation at the application layer
class LogType(str, Enum):
    REASONING = "REASONING"
    TOOL_CALL = "TOOL_CALL"


class LlmLogBase(BaseModel):
    plan_id: str | UUID4 | None = None
    log_type: str | None = None
    time_created: datetime | None = None
    content: dict | None = None
    

class LlmLogCreate(LlmLogBase):
    log_type: LogType = LogType.REASONING


class LlmLogUpdate(LlmLogBase):
    pass


class LlmLogCreated(LlmLogBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


class LlmLog(LlmLogBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | str


ManualTimelineTask.model_rebuild()
Issue.model_rebuild()
CertificateAuthority.model_rebuild()
CertificateTemplate.model_rebuild()
Action.model_rebuild()
WaitForTask.model_rebuild()
RunJob.model_rebuild()
Domain.model_rebuild()
File.model_rebuild()
Proxy.model_rebuild()
Credential.model_rebuild()
Password.model_rebuild()
Host.model_rebuild()
Process.model_rebuild()
ProxyChain.model_rebuild()
ChainStep.model_rebuild()
C2Job.model_rebuild()
ProxyJob.model_rebuild()
C2Implant.model_rebuild()
C2Task.model_rebuild()
ProxyChainGraph.model_rebuild()
Kerberos.model_rebuild()
Share.model_rebuild()
ShareFile.model_rebuild()
Hash.model_rebuild()
C2ServerCommand.model_rebuild()
PlaybookStepModifier.model_rebuild()
Highlight.model_rebuild()
ParseResult.model_rebuild()
PlaybookTemplateView.model_rebuild()
C2OutputCreate.model_rebuild()
C2ServerType.model_rebuild()
HarbingerYaml.model_rebuild()
Suggestion.model_rebuild()
Checklist.model_rebuild()
PlanStep.model_rebuild()
Plan.model_rebuild()
