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

from enum import Enum
from typing import Dict, Type

from harbinger.job_templates.proxy.base import JobTemplateModel
from harbinger.job_templates.proxy import schemas


PROXY_JOB_BASE_MAP: Dict[str, Type[JobTemplateModel]] = {
    "secretsdump": schemas.SecretsDump,
    "upload_file": schemas.UploadFile,
    "smbclient": schemas.SMBClient,
    "certipy_find": schemas.CertipyFind,
    "wmiexec": schemas.WmiExec,
    "atexec": schemas.AtExec,
    # "sharphound": schemas.SharpHound,
    # "snuffles": schemas.Snuffles,
    "bloodhound_python": schemas.BloodHoundPython,
    "download_file": schemas.DownloadFile,
    "pywhisker": schemas.PyWhisker,
    "echo": schemas.TestTemplate,
    "list_processes": schemas.ListProcesses,
    "custom": schemas.Custom,
}
