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

import unittest
from unittest import mock

from harbinger.worker.output import OUTPUT_PARSERS, EnvParser, IPConfigParser

ipconfig_data = """{6929494D-CB96-4E0C-AE4C-3FB5DF62D6C0}
	Ethernet
	Intel(R) PRO/1000 MT Network Connection
	D6-13-C9-8C-28-F0
	10.0.2.5
Hostname: 	PC1
DNS Suffix: 	blarg.local
DNS Server: 	10.0.2.2
		8.8.8.8
"""

env_data = r"""Gathering Process Environment Variables:

=::=::\
ALLUSERSPROFILE=C:\ProgramData
APPDATA=C:\Users\development\AppData\Roaming
CLIENTNAME=SW1-111174
CommonProgramFiles=C:\Program Files\Common Files
CommonProgramFiles(x86)=C:\Program Files (x86)\Common Files
CommonProgramW6432=C:\Program Files\Common Files
COMPUTERNAME=PC1
ComSpec=C:\WINDOWS\system32\cmd.exe
DriverData=C:\Windows\System32\Drivers\DriverData
FPS_BROWSER_APP_PROFILE_STRING=Internet Explorer
FPS_BROWSER_USER_PROFILE_STRING=Default
HOMEDRIVE=C:
HOMEPATH=\Users\development
LOCALAPPDATA=C:\Users\development\AppData\Local
LOGONSERVER=\\DC01
NUMBER_OF_PROCESSORS=1
OneDrive=C:\Users\development\OneDrive
OS=Windows_NT
Path=C:\WINDOWS\system32;C:\WINDOWS;C:\WINDOWS\System32\Wbem;C:\WINDOWS\System32\WindowsPowerShell\v1.0\;C:\WINDOWS\System32\OpenSSH\;C:\Program Files\Microsoft VS Code\bin;C:\Users\development\AppData\Local\Microsoft\WindowsApps;C:\Users\development\AppData\Local\Programs\Git\cmd;
PATHEXT=.COM;.EXE;.BAT;.CMD;.VBS;.VBE;.JS;.JSE;.WSF;.WSH;.MSC;.CPL
PROCESSOR_ARCHITECTURE=AMD64
PROCESSOR_IDENTIFIER=AMD64 Family 15 Model 6 Stepping 1, AuthenticAMD
PROCESSOR_LEVEL=15
PROCESSOR_REVISION=0601
ProgramData=C:\ProgramData
ProgramFiles=C:\Program Files
ProgramFiles(x86)=C:\Program Files (x86)
ProgramW6432=C:\Program Files
PSModulePath=C:\Users\development\Documents\WindowsPowerShell\Modules;C:\Program Files\WindowsPowerShell\Modules;C:\WINDOWS\system32\WindowsPowerShell\v1.0\Modules
PUBLIC=C:\Users\Public
SESSIONNAME=RDP-Tcp#1
SystemDrive=C:
SystemRoot=C:\WINDOWS
TEMP=C:\Users\DEVELO~1\AppData\Local\Temp
TMP=C:\Users\DEVELO~1\AppData\Local\Temp
USERDNSDOMAIN=BLARG.LOCAL
USERDOMAIN=BLARG
USERDOMAIN_ROAMINGPROFILE=BLARG"""


class TestMythicC2(unittest.IsolatedAsyncioTestCase):
    def test_output_parsers(self):
        for parser in OUTPUT_PARSERS:
            p = parser(mock.AsyncMock)
            assert isinstance(p.needle, list)
            assert p.needle != []

    def test_parser_list_unique(self):
        assert len(OUTPUT_PARSERS) == len(set(OUTPUT_PARSERS))

    async def test_ipconfig(self):
        p = IPConfigParser(mock.AsyncMock)
        res = await p.match(ipconfig_data)
        assert res, "IPConfigParser doesn't match on ipconfig output"

        res = await p.match(env_data)
        assert not res, "IPConfigParser does match on env output"

    async def test_env(self):
        p = EnvParser(mock.AsyncMock)
        res = await p.match(env_data)
        assert res, "EnvParser doesn't match on env output"

        res = await p.match(ipconfig_data)
        assert not res, "EnvParser does match on ipconfig output"
