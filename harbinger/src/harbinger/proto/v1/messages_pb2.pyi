from collections.abc import Iterable as _Iterable
from collections.abc import Mapping as _Mapping
from typing import (
    ClassVar as _ClassVar,
)

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper

DESCRIPTOR: _descriptor.FileDescriptor

class OutputType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OUTPUT_TYPE_UNSPECIFIED: _ClassVar[OutputType]
    OUTPUT_TYPE_STDOUT: _ClassVar[OutputType]
    OUTPUT_TYPE_STDERR: _ClassVar[OutputType]

OUTPUT_TYPE_UNSPECIFIED: OutputType
OUTPUT_TYPE_STDOUT: OutputType
OUTPUT_TYPE_STDERR: OutputType

class PingRequest(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: str | None = ...) -> None: ...

class ImplantRequest(_message.Message):
    __slots__ = (
        "architecture",
        "c2_server_id",
        "c2_type",
        "description",
        "domain",
        "external_ip",
        "hostname",
        "internal_id",
        "ip",
        "jitter",
        "last_checkin",
        "name",
        "os",
        "payload_type",
        "pid",
        "process",
        "sleep",
        "username",
    )
    C2_SERVER_ID_FIELD_NUMBER: _ClassVar[int]
    INTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    C2_TYPE_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    HOSTNAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    SLEEP_FIELD_NUMBER: _ClassVar[int]
    JITTER_FIELD_NUMBER: _ClassVar[int]
    OS_FIELD_NUMBER: _ClassVar[int]
    PID_FIELD_NUMBER: _ClassVar[int]
    ARCHITECTURE_FIELD_NUMBER: _ClassVar[int]
    PROCESS_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    IP_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_IP_FIELD_NUMBER: _ClassVar[int]
    DOMAIN_FIELD_NUMBER: _ClassVar[int]
    LAST_CHECKIN_FIELD_NUMBER: _ClassVar[int]
    c2_server_id: str
    internal_id: str
    c2_type: str
    payload_type: str
    name: str
    hostname: str
    description: str
    sleep: int
    jitter: int
    os: str
    pid: int
    architecture: str
    process: str
    username: str
    ip: str
    external_ip: str
    domain: str
    last_checkin: str
    def __init__(
        self,
        c2_server_id: str | None = ...,
        internal_id: str | None = ...,
        c2_type: str | None = ...,
        payload_type: str | None = ...,
        name: str | None = ...,
        hostname: str | None = ...,
        description: str | None = ...,
        sleep: int | None = ...,
        jitter: int | None = ...,
        os: str | None = ...,
        pid: int | None = ...,
        architecture: str | None = ...,
        process: str | None = ...,
        username: str | None = ...,
        ip: str | None = ...,
        external_ip: str | None = ...,
        domain: str | None = ...,
        last_checkin: str | None = ...,
    ) -> None: ...

class ImplantResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ProxyRequest(_message.Message):
    __slots__ = (
        "c2_server_id",
        "host",
        "internal_id",
        "note",
        "password",
        "port",
        "remote_hostname",
        "status",
        "type",
        "username",
    )
    HOST_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    NOTE_FIELD_NUMBER: _ClassVar[int]
    REMOTE_HOSTNAME_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    C2_SERVER_ID_FIELD_NUMBER: _ClassVar[int]
    INTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    host: str
    port: int
    type: str
    status: str
    note: str
    remote_hostname: str
    username: str
    password: str
    c2_server_id: str
    internal_id: str
    def __init__(
        self,
        host: str | None = ...,
        port: int | None = ...,
        type: str | None = ...,
        status: str | None = ...,
        note: str | None = ...,
        remote_hostname: str | None = ...,
        username: str | None = ...,
        password: str | None = ...,
        c2_server_id: str | None = ...,
        internal_id: str | None = ...,
    ) -> None: ...

class ProxyResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class FileRequest(_message.Message):
    __slots__ = (
        "bucket",
        "c2_server_id",
        "filename",
        "internal_implant_id",
        "internal_task_id",
        "path",
        "upload_file_id",
    )
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    INTERNAL_TASK_ID_FIELD_NUMBER: _ClassVar[int]
    C2_SERVER_ID_FIELD_NUMBER: _ClassVar[int]
    INTERNAL_IMPLANT_ID_FIELD_NUMBER: _ClassVar[int]
    UPLOAD_FILE_ID_FIELD_NUMBER: _ClassVar[int]
    filename: str
    bucket: str
    path: str
    internal_task_id: str
    c2_server_id: str
    internal_implant_id: str
    upload_file_id: str
    def __init__(
        self,
        filename: str | None = ...,
        bucket: str | None = ...,
        path: str | None = ...,
        internal_task_id: str | None = ...,
        c2_server_id: str | None = ...,
        internal_implant_id: str | None = ...,
        upload_file_id: str | None = ...,
    ) -> None: ...

class FileResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: str | None = ...) -> None: ...

class C2TaskStatusRequest(_message.Message):
    __slots__ = ("c2_server_id", "c2_task_id", "message", "status")
    C2_SERVER_ID_FIELD_NUMBER: _ClassVar[int]
    C2_TASK_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    c2_server_id: str
    c2_task_id: str
    status: str
    message: str
    def __init__(
        self,
        c2_server_id: str | None = ...,
        c2_task_id: str | None = ...,
        status: str | None = ...,
        message: str | None = ...,
    ) -> None: ...

class C2TaskStatusResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SettingsRequest(_message.Message):
    __slots__ = ("c2_server_id",)
    C2_SERVER_ID_FIELD_NUMBER: _ClassVar[int]
    c2_server_id: str
    def __init__(self, c2_server_id: str | None = ...) -> None: ...

class SettingsResponse(_message.Message):
    __slots__ = (
        "ca_certificate",
        "certificate",
        "hostname",
        "name",
        "password",
        "port",
        "private_key",
        "token",
        "type",
        "username",
    )
    TYPE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    HOSTNAME_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    PASSWORD_FIELD_NUMBER: _ClassVar[int]
    CA_CERTIFICATE_FIELD_NUMBER: _ClassVar[int]
    PRIVATE_KEY_FIELD_NUMBER: _ClassVar[int]
    TOKEN_FIELD_NUMBER: _ClassVar[int]
    CERTIFICATE_FIELD_NUMBER: _ClassVar[int]
    type: str
    name: str
    hostname: str
    username: str
    port: int
    password: str
    ca_certificate: str
    private_key: str
    token: str
    certificate: str
    def __init__(
        self,
        type: str | None = ...,
        name: str | None = ...,
        hostname: str | None = ...,
        username: str | None = ...,
        port: int | None = ...,
        password: str | None = ...,
        ca_certificate: str | None = ...,
        private_key: str | None = ...,
        token: str | None = ...,
        certificate: str | None = ...,
    ) -> None: ...

class TaskRequest(_message.Message):
    __slots__ = (
        "c2_server_id",
        "command_name",
        "display_params",
        "internal_id",
        "internal_implant_id",
        "operator",
        "original_params",
        "status",
        "time_completed",
        "time_started",
    )
    INTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    C2_SERVER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ORIGINAL_PARAMS_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_PARAMS_FIELD_NUMBER: _ClassVar[int]
    TIME_STARTED_FIELD_NUMBER: _ClassVar[int]
    TIME_COMPLETED_FIELD_NUMBER: _ClassVar[int]
    COMMAND_NAME_FIELD_NUMBER: _ClassVar[int]
    OPERATOR_FIELD_NUMBER: _ClassVar[int]
    INTERNAL_IMPLANT_ID_FIELD_NUMBER: _ClassVar[int]
    internal_id: str
    c2_server_id: str
    status: str
    original_params: str
    display_params: str
    time_started: str
    time_completed: str
    command_name: str
    operator: str
    internal_implant_id: str
    def __init__(
        self,
        internal_id: str | None = ...,
        c2_server_id: str | None = ...,
        status: str | None = ...,
        original_params: str | None = ...,
        display_params: str | None = ...,
        time_started: str | None = ...,
        time_completed: str | None = ...,
        command_name: str | None = ...,
        operator: str | None = ...,
        internal_implant_id: str | None = ...,
    ) -> None: ...

class TaskResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Process(_message.Message):
    __slots__ = (
        "architecture",
        "bin_path",
        "command_line",
        "description",
        "handle",
        "name",
        "parent_process_id",
        "process_id",
        "user",
    )
    PROCESS_ID_FIELD_NUMBER: _ClassVar[int]
    ARCHITECTURE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    BIN_PATH_FIELD_NUMBER: _ClassVar[int]
    PARENT_PROCESS_ID_FIELD_NUMBER: _ClassVar[int]
    COMMAND_LINE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    HANDLE_FIELD_NUMBER: _ClassVar[int]
    process_id: int
    architecture: str
    name: str
    user: str
    bin_path: str
    parent_process_id: int
    command_line: str
    description: str
    handle: str
    def __init__(
        self,
        process_id: int | None = ...,
        architecture: str | None = ...,
        name: str | None = ...,
        user: str | None = ...,
        bin_path: str | None = ...,
        parent_process_id: int | None = ...,
        command_line: str | None = ...,
        description: str | None = ...,
        handle: str | None = ...,
    ) -> None: ...

class ShareFile(_message.Message):
    __slots__ = (
        "created",
        "last_accessed",
        "last_modified",
        "name",
        "size",
        "type",
        "unc_path",
    )
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    LAST_ACCESSED_FIELD_NUMBER: _ClassVar[int]
    LAST_MODIFIED_FIELD_NUMBER: _ClassVar[int]
    CREATED_FIELD_NUMBER: _ClassVar[int]
    UNC_PATH_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    type: str
    size: int
    last_accessed: str
    last_modified: str
    created: str
    unc_path: str
    name: str
    def __init__(
        self,
        type: str | None = ...,
        size: int | None = ...,
        last_accessed: str | None = ...,
        last_modified: str | None = ...,
        created: str | None = ...,
        unc_path: str | None = ...,
        name: str | None = ...,
    ) -> None: ...

class FileList(_message.Message):
    __slots__ = (
        "created",
        "files",
        "host",
        "last_accessed",
        "last_modified",
        "name",
        "parent_path",
        "size",
        "unc_path",
    )
    HOST_FIELD_NUMBER: _ClassVar[int]
    PARENT_PATH_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    UNC_PATH_FIELD_NUMBER: _ClassVar[int]
    SIZE_FIELD_NUMBER: _ClassVar[int]
    LAST_ACCESSED_FIELD_NUMBER: _ClassVar[int]
    LAST_MODIFIED_FIELD_NUMBER: _ClassVar[int]
    CREATED_FIELD_NUMBER: _ClassVar[int]
    FILES_FIELD_NUMBER: _ClassVar[int]
    host: str
    parent_path: str
    name: str
    unc_path: str
    size: int
    last_accessed: str
    last_modified: str
    created: str
    files: _containers.RepeatedCompositeFieldContainer[ShareFile]
    def __init__(
        self,
        host: str | None = ...,
        parent_path: str | None = ...,
        name: str | None = ...,
        unc_path: str | None = ...,
        size: int | None = ...,
        last_accessed: str | None = ...,
        last_modified: str | None = ...,
        created: str | None = ...,
        files: _Iterable[ShareFile | _Mapping] | None = ...,
    ) -> None: ...

class TaskOutputRequest(_message.Message):
    __slots__ = (
        "bucket",
        "c2_server_id",
        "file_list",
        "internal_id",
        "internal_task_id",
        "output_type",
        "path",
        "processes",
        "response_text",
        "timestamp",
    )
    INTERNAL_ID_FIELD_NUMBER: _ClassVar[int]
    C2_SERVER_ID_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_TEXT_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_TYPE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    INTERNAL_TASK_ID_FIELD_NUMBER: _ClassVar[int]
    BUCKET_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    PROCESSES_FIELD_NUMBER: _ClassVar[int]
    FILE_LIST_FIELD_NUMBER: _ClassVar[int]
    internal_id: str
    c2_server_id: str
    response_text: str
    output_type: str
    timestamp: str
    internal_task_id: str
    bucket: str
    path: str
    processes: _containers.RepeatedCompositeFieldContainer[Process]
    file_list: FileList
    def __init__(
        self,
        internal_id: str | None = ...,
        c2_server_id: str | None = ...,
        response_text: str | None = ...,
        output_type: str | None = ...,
        timestamp: str | None = ...,
        internal_task_id: str | None = ...,
        bucket: str | None = ...,
        path: str | None = ...,
        processes: _Iterable[Process | _Mapping] | None = ...,
        file_list: FileList | _Mapping | None = ...,
    ) -> None: ...

class TaskOutputResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PingResponse(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: str | None = ...) -> None: ...

class Event(_message.Message):
    __slots__ = ("chain_status", "event", "id", "name", "progress")
    EVENT_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CHAIN_STATUS_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    event: str
    id: str
    name: str
    chain_status: str
    progress: Progress
    def __init__(
        self,
        event: str | None = ...,
        id: str | None = ...,
        name: str | None = ...,
        chain_status: str | None = ...,
        progress: Progress | _Mapping | None = ...,
    ) -> None: ...

class Progress(_message.Message):
    __slots__ = ("current", "description", "id", "max", "percentage", "type")
    ID_FIELD_NUMBER: _ClassVar[int]
    CURRENT_FIELD_NUMBER: _ClassVar[int]
    MAX_FIELD_NUMBER: _ClassVar[int]
    PERCENTAGE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    id: str
    current: int
    max: int
    percentage: float
    type: str
    description: str
    def __init__(
        self,
        id: str | None = ...,
        current: int | None = ...,
        max: int | None = ...,
        percentage: float | None = ...,
        type: str | None = ...,
        description: str | None = ...,
    ) -> None: ...

class Arguments(_message.Message):
    __slots__ = ("arguments",)
    ARGUMENTS_FIELD_NUMBER: _ClassVar[int]
    arguments: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, arguments: _Iterable[str] | None = ...) -> None: ...

class Output(_message.Message):
    __slots__ = ("created_at", "id", "job_id", "output", "type")
    ID_FIELD_NUMBER: _ClassVar[int]
    JOB_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    id: str
    job_id: str
    type: OutputType
    output: str
    created_at: int
    def __init__(
        self,
        id: str | None = ...,
        job_id: str | None = ...,
        type: OutputType | str | None = ...,
        output: str | None = ...,
        created_at: int | None = ...,
    ) -> None: ...

class FileExistsRequest(_message.Message):
    __slots__ = ("md5", "sha1", "sha256")
    MD5_FIELD_NUMBER: _ClassVar[int]
    SHA1_FIELD_NUMBER: _ClassVar[int]
    SHA256_FIELD_NUMBER: _ClassVar[int]
    md5: str
    sha1: str
    sha256: str
    def __init__(
        self,
        md5: str | None = ...,
        sha1: str | None = ...,
        sha256: str | None = ...,
    ) -> None: ...

class FileExistsResponse(_message.Message):
    __slots__ = ("exists",)
    EXISTS_FIELD_NUMBER: _ClassVar[int]
    exists: bool
    def __init__(self, exists: bool = ...) -> None: ...

class UploadFileRequest(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    def __init__(self, data: bytes | None = ...) -> None: ...

class UploadFileResponse(_message.Message):
    __slots__ = ("upload_file_id",)
    UPLOAD_FILE_ID_FIELD_NUMBER: _ClassVar[int]
    upload_file_id: str
    def __init__(self, upload_file_id: str | None = ...) -> None: ...

class DownloadFileRequest(_message.Message):
    __slots__ = ("file_id",)
    FILE_ID_FIELD_NUMBER: _ClassVar[int]
    file_id: str
    def __init__(self, file_id: str | None = ...) -> None: ...

class DownloadFileResponse(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    def __init__(self, data: bytes | None = ...) -> None: ...

class C2ServerStatusRequest(_message.Message):
    __slots__ = ("c2_server_id", "name", "status")
    C2_SERVER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    c2_server_id: str
    status: str
    name: str
    def __init__(
        self,
        c2_server_id: str | None = ...,
        status: str | None = ...,
        name: str | None = ...,
    ) -> None: ...

class C2ServerStatusResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
