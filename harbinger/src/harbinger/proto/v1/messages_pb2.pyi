from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import (
    ClassVar as _ClassVar,
    Iterable as _Iterable,
    Mapping as _Mapping,
    Optional as _Optional,
    Union as _Union,
)

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
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class ImplantRequest(_message.Message):
    __slots__ = (
        "c2_server_id",
        "internal_id",
        "c2_type",
        "payload_type",
        "name",
        "hostname",
        "description",
        "sleep",
        "jitter",
        "os",
        "pid",
        "architecture",
        "process",
        "username",
        "ip",
        "external_ip",
        "domain",
        "last_checkin",
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
        c2_server_id: _Optional[str] = ...,
        internal_id: _Optional[str] = ...,
        c2_type: _Optional[str] = ...,
        payload_type: _Optional[str] = ...,
        name: _Optional[str] = ...,
        hostname: _Optional[str] = ...,
        description: _Optional[str] = ...,
        sleep: _Optional[int] = ...,
        jitter: _Optional[int] = ...,
        os: _Optional[str] = ...,
        pid: _Optional[int] = ...,
        architecture: _Optional[str] = ...,
        process: _Optional[str] = ...,
        username: _Optional[str] = ...,
        ip: _Optional[str] = ...,
        external_ip: _Optional[str] = ...,
        domain: _Optional[str] = ...,
        last_checkin: _Optional[str] = ...,
    ) -> None: ...

class ImplantResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ProxyRequest(_message.Message):
    __slots__ = (
        "host",
        "port",
        "type",
        "status",
        "note",
        "remote_hostname",
        "username",
        "password",
        "c2_server_id",
        "internal_id",
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
        host: _Optional[str] = ...,
        port: _Optional[int] = ...,
        type: _Optional[str] = ...,
        status: _Optional[str] = ...,
        note: _Optional[str] = ...,
        remote_hostname: _Optional[str] = ...,
        username: _Optional[str] = ...,
        password: _Optional[str] = ...,
        c2_server_id: _Optional[str] = ...,
        internal_id: _Optional[str] = ...,
    ) -> None: ...

class ProxyResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class FileRequest(_message.Message):
    __slots__ = (
        "filename",
        "bucket",
        "path",
        "internal_task_id",
        "c2_server_id",
        "internal_implant_id",
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
        filename: _Optional[str] = ...,
        bucket: _Optional[str] = ...,
        path: _Optional[str] = ...,
        internal_task_id: _Optional[str] = ...,
        c2_server_id: _Optional[str] = ...,
        internal_implant_id: _Optional[str] = ...,
        upload_file_id: _Optional[str] = ...,
    ) -> None: ...

class FileResponse(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class C2TaskStatusRequest(_message.Message):
    __slots__ = ("c2_server_id", "c2_task_id", "status", "message")
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
        c2_server_id: _Optional[str] = ...,
        c2_task_id: _Optional[str] = ...,
        status: _Optional[str] = ...,
        message: _Optional[str] = ...,
    ) -> None: ...

class C2TaskStatusResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class SettingsRequest(_message.Message):
    __slots__ = ("c2_server_id",)
    C2_SERVER_ID_FIELD_NUMBER: _ClassVar[int]
    c2_server_id: str
    def __init__(self, c2_server_id: _Optional[str] = ...) -> None: ...

class SettingsResponse(_message.Message):
    __slots__ = (
        "type",
        "name",
        "hostname",
        "username",
        "port",
        "password",
        "ca_certificate",
        "private_key",
        "token",
        "certificate",
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
        type: _Optional[str] = ...,
        name: _Optional[str] = ...,
        hostname: _Optional[str] = ...,
        username: _Optional[str] = ...,
        port: _Optional[int] = ...,
        password: _Optional[str] = ...,
        ca_certificate: _Optional[str] = ...,
        private_key: _Optional[str] = ...,
        token: _Optional[str] = ...,
        certificate: _Optional[str] = ...,
    ) -> None: ...

class TaskRequest(_message.Message):
    __slots__ = (
        "internal_id",
        "c2_server_id",
        "status",
        "original_params",
        "display_params",
        "time_started",
        "time_completed",
        "command_name",
        "operator",
        "internal_implant_id",
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
        internal_id: _Optional[str] = ...,
        c2_server_id: _Optional[str] = ...,
        status: _Optional[str] = ...,
        original_params: _Optional[str] = ...,
        display_params: _Optional[str] = ...,
        time_started: _Optional[str] = ...,
        time_completed: _Optional[str] = ...,
        command_name: _Optional[str] = ...,
        operator: _Optional[str] = ...,
        internal_implant_id: _Optional[str] = ...,
    ) -> None: ...

class TaskResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Process(_message.Message):
    __slots__ = (
        "process_id",
        "architecture",
        "name",
        "user",
        "bin_path",
        "parent_process_id",
        "command_line",
        "description",
        "handle",
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
        process_id: _Optional[int] = ...,
        architecture: _Optional[str] = ...,
        name: _Optional[str] = ...,
        user: _Optional[str] = ...,
        bin_path: _Optional[str] = ...,
        parent_process_id: _Optional[int] = ...,
        command_line: _Optional[str] = ...,
        description: _Optional[str] = ...,
        handle: _Optional[str] = ...,
    ) -> None: ...

class ShareFile(_message.Message):
    __slots__ = (
        "type",
        "size",
        "last_accessed",
        "last_modified",
        "created",
        "unc_path",
        "name",
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
        type: _Optional[str] = ...,
        size: _Optional[int] = ...,
        last_accessed: _Optional[str] = ...,
        last_modified: _Optional[str] = ...,
        created: _Optional[str] = ...,
        unc_path: _Optional[str] = ...,
        name: _Optional[str] = ...,
    ) -> None: ...

class FileList(_message.Message):
    __slots__ = (
        "host",
        "parent_path",
        "name",
        "unc_path",
        "size",
        "last_accessed",
        "last_modified",
        "created",
        "files",
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
        host: _Optional[str] = ...,
        parent_path: _Optional[str] = ...,
        name: _Optional[str] = ...,
        unc_path: _Optional[str] = ...,
        size: _Optional[int] = ...,
        last_accessed: _Optional[str] = ...,
        last_modified: _Optional[str] = ...,
        created: _Optional[str] = ...,
        files: _Optional[_Iterable[_Union[ShareFile, _Mapping]]] = ...,
    ) -> None: ...

class TaskOutputRequest(_message.Message):
    __slots__ = (
        "internal_id",
        "c2_server_id",
        "response_text",
        "output_type",
        "timestamp",
        "internal_task_id",
        "bucket",
        "path",
        "processes",
        "file_list",
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
        internal_id: _Optional[str] = ...,
        c2_server_id: _Optional[str] = ...,
        response_text: _Optional[str] = ...,
        output_type: _Optional[str] = ...,
        timestamp: _Optional[str] = ...,
        internal_task_id: _Optional[str] = ...,
        bucket: _Optional[str] = ...,
        path: _Optional[str] = ...,
        processes: _Optional[_Iterable[_Union[Process, _Mapping]]] = ...,
        file_list: _Optional[_Union[FileList, _Mapping]] = ...,
    ) -> None: ...

class TaskOutputResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PingResponse(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class Event(_message.Message):
    __slots__ = ("event", "id", "name", "chain_status", "progress")
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
        event: _Optional[str] = ...,
        id: _Optional[str] = ...,
        name: _Optional[str] = ...,
        chain_status: _Optional[str] = ...,
        progress: _Optional[_Union[Progress, _Mapping]] = ...,
    ) -> None: ...

class Progress(_message.Message):
    __slots__ = ("id", "current", "max", "percentage", "type", "description")
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
        id: _Optional[str] = ...,
        current: _Optional[int] = ...,
        max: _Optional[int] = ...,
        percentage: _Optional[float] = ...,
        type: _Optional[str] = ...,
        description: _Optional[str] = ...,
    ) -> None: ...

class Arguments(_message.Message):
    __slots__ = ("arguments",)
    ARGUMENTS_FIELD_NUMBER: _ClassVar[int]
    arguments: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, arguments: _Optional[_Iterable[str]] = ...) -> None: ...

class Output(_message.Message):
    __slots__ = ("id", "job_id", "type", "output", "created_at")
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
        id: _Optional[str] = ...,
        job_id: _Optional[str] = ...,
        type: _Optional[_Union[OutputType, str]] = ...,
        output: _Optional[str] = ...,
        created_at: _Optional[int] = ...,
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
        md5: _Optional[str] = ...,
        sha1: _Optional[str] = ...,
        sha256: _Optional[str] = ...,
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
    def __init__(self, data: _Optional[bytes] = ...) -> None: ...

class UploadFileResponse(_message.Message):
    __slots__ = ("upload_file_id",)
    UPLOAD_FILE_ID_FIELD_NUMBER: _ClassVar[int]
    upload_file_id: str
    def __init__(self, upload_file_id: _Optional[str] = ...) -> None: ...

class DownloadFileRequest(_message.Message):
    __slots__ = ("file_id",)
    FILE_ID_FIELD_NUMBER: _ClassVar[int]
    file_id: str
    def __init__(self, file_id: _Optional[str] = ...) -> None: ...

class DownloadFileResponse(_message.Message):
    __slots__ = ("data",)
    DATA_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    def __init__(self, data: _Optional[bytes] = ...) -> None: ...

class C2ServerStatusRequest(_message.Message):
    __slots__ = ("c2_server_id", "status", "name")
    C2_SERVER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    c2_server_id: str
    status: str
    name: str
    def __init__(
        self,
        c2_server_id: _Optional[str] = ...,
        status: _Optional[str] = ...,
        name: _Optional[str] = ...,
    ) -> None: ...

class C2ServerStatusResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
