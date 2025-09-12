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

from harbinger.schemas import FileList, ShareFileCreate


class TestFileListParser(unittest.IsolatedAsyncioTestCase):
    async def test_file_parser_local_path(self):
        file_list = FileList(
            host="host1",
            parent_path="C:\\Users\\user1",
            name="Desktop",
            files=[
                ShareFileCreate(
                    type="file",
                    name="test.exe",
                    size=123,
                ),
            ],
            size=4096,
        )

        file_list.parse()

        assert file_list.sharename == "C$"
        assert file_list.share_unc_path == "\\\\host1\\C$"
        assert file_list.unc_path == "\\\\host1\\C$\\Users\\user1\\Desktop"
        assert file_list.depth == 3

        # Check parents
        assert file_list.parents is not None
        if file_list.parents:
            assert len(file_list.parents) == 3
            assert file_list.parents[0].name == ""
            assert file_list.parents[0].unc_path == "\\\\host1\\C$"
            assert file_list.parents[0].depth == 0
            assert file_list.parents[1].name == "Users"
            assert file_list.parents[1].unc_path == "\\\\host1\\C$\\Users"
            assert file_list.parents[1].depth == 1
            assert file_list.parents[2].name == "user1"
            assert file_list.parents[2].unc_path == "\\\\host1\\C$\\Users\\user1"
            assert file_list.parents[2].depth == 2

        # Check files
        assert file_list.files is not None
        if file_list.files:
            assert len(file_list.files) == 1
            assert file_list.files[0].name == "test.exe"
            assert file_list.files[0].unc_path == "\\\\host1\\C$\\Users\\user1\\Desktop\\test.exe"
            assert file_list.files[0].depth == 3
            assert file_list.files[0].extension == "exe"

    async def test_file_parser_unc_parent_path(self):
        file_list = FileList(
            host="host1",
            parent_path="\\\\host1\\C$\\Users\\user1",
            name="Desktop",
            files=[
                ShareFileCreate(
                    type="file",
                    name="test.exe",
                    size=123,
                ),
            ],
            size=4096,
        )
        file_list.parse()

        assert file_list.sharename == "C$"
        assert file_list.share_unc_path == "\\\\host1\\C$"
        assert file_list.unc_path == "\\\\host1\\C$\\Users\\user1\\Desktop"
        assert file_list.depth == 3
        assert file_list.domain == ""

        # Check parents
        assert file_list.parents is not None
        if file_list.parents:
            assert len(file_list.parents) == 3
            assert file_list.parents[0].name == ""
            assert file_list.parents[0].unc_path == "\\\\host1\\C$"
            assert file_list.parents[0].depth == 0
            assert file_list.parents[1].name == "Users"
            assert file_list.parents[1].unc_path == "\\\\host1\\C$\\Users"
            assert file_list.parents[1].depth == 1
            assert file_list.parents[2].name == "user1"
            assert file_list.parents[2].unc_path == "\\\\host1\\C$\\Users\\user1"
            assert file_list.parents[2].depth == 2

        # Check files
        assert file_list.files is not None
        if file_list.files:
            assert len(file_list.files) == 1
            assert file_list.files[0].name == "test.exe"
            assert file_list.files[0].unc_path == "\\\\host1\\C$\\Users\\user1\\Desktop\\test.exe"
            assert file_list.files[0].depth == 3
            assert file_list.files[0].extension == "exe"

    async def test_file_parser_unc_name(self):
        file_list = FileList(
            host="host1",
            parent_path="",
            name="\\\\host1\\C$\\Users\\user1\\Desktop",
            files=[
                ShareFileCreate(
                    type="file",
                    name="test.exe",
                    size=123,
                ),
            ],
            size=4096,
        )
        file_list.parse()

        assert file_list.sharename == "C$"
        assert file_list.share_unc_path == "\\\\host1\\C$"
        assert file_list.unc_path == "\\\\host1\\C$\\Users\\user1\\Desktop"
        assert file_list.depth == 3
        assert file_list.host == "host1"
        assert file_list.domain == ""

        # Check parents
        assert file_list.parents is not None
        if file_list.parents:
            assert len(file_list.parents) == 3
            assert file_list.parents[0].name == ""
            assert file_list.parents[0].unc_path == "\\\\host1\\C$"
            assert file_list.parents[0].depth == 0
            assert file_list.parents[1].name == "Users"
            assert file_list.parents[1].unc_path == "\\\\host1\\C$\\Users"
            assert file_list.parents[1].depth == 1
            assert file_list.parents[2].name == "user1"
            assert file_list.parents[2].unc_path == "\\\\host1\\C$\\Users\\user1"
            assert file_list.parents[2].depth == 2

        # Check files
        assert file_list.files is not None
        if file_list.files:
            assert len(file_list.files) == 1
            assert file_list.files[0].name == "test.exe"
            assert file_list.files[0].unc_path == "\\\\host1\\C$\\Users\\user1\\Desktop\\test.exe"
            assert file_list.files[0].depth == 3
            assert file_list.files[0].extension == "exe"

    async def test_file_parser_root_share(self):
        file_list = FileList(
            host="host1",
            parent_path="\\\\host1\\C$",
            name="",
            size=4096,
        )
        file_list.parse()

        assert file_list.sharename == "C$"
        assert file_list.share_unc_path == "\\\\host1\\C$"
        assert file_list.unc_path == "\\\\host1\\C$"
        assert file_list.depth == 0
        assert file_list.domain == ""

        # Check parents
        assert file_list.parents is not None
        if file_list.parents:
            assert len(file_list.parents) == 1
            assert file_list.parents[0].name == ""
            assert file_list.parents[0].unc_path == "\\\\host1\\C$"
            assert file_list.parents[0].depth == 0

    async def test_file_parser_netlogon_share(self):
        file_list = FileList(
            host="HOST1.DOMAIN.LOCAL",
            parent_path="\\\\HOST1.DOMAIN.LOCAL",
            name="NETLOGON",
            size=0,
            files=[
                ShareFileCreate(
                    type="file",
                    name="script1.ps1",
                    size=123,
                ),
                ShareFileCreate(
                    type="file",
                    name="script2.ps1",
                    size=123,
                ),
            ],
        )
        file_list.parse()

        assert file_list.sharename == "NETLOGON"
        assert file_list.share_unc_path == "\\\\HOST1.DOMAIN.LOCAL\\NETLOGON"
        assert file_list.unc_path == "\\\\HOST1.DOMAIN.LOCAL\\NETLOGON"
        assert file_list.depth == 0
        assert file_list.host == "HOST1"
        assert file_list.domain == "DOMAIN.LOCAL"

        # Check parents (should only have the root share)
        assert file_list.parents is not None
        if file_list.parents:
            assert len(file_list.parents) == 1
            assert file_list.parents[0].name == ""
            assert file_list.parents[0].unc_path == "\\\\HOST1.DOMAIN.LOCAL\\NETLOGON"
            assert file_list.parents[0].depth == 0

        # Check files
        assert file_list.files is not None
        if file_list.files:
            assert len(file_list.files) == 2
            assert file_list.files[0].name == "script1.ps1"
            assert file_list.files[0].unc_path == "\\\\HOST1.DOMAIN.LOCAL\\NETLOGON\\script1.ps1"
            assert file_list.files[0].depth == 0
            assert file_list.files[0].extension == "ps1"
            assert file_list.files[1].name == "script2.ps1"
            assert file_list.files[1].unc_path == "\\\\HOST1.DOMAIN.LOCAL\\NETLOGON\\script2.ps1"
            assert file_list.files[1].depth == 0
            assert file_list.files[1].extension == "ps1"
