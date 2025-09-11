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
from harbinger.config.process import get_process_mapping
from harbinger import schemas


class TestProcesses(unittest.TestCase):
    def test_processes(self):
        result = get_process_mapping()
        self.assertGreater(len(result), 0)

    def test_processbase(self):
        process_x64 = schemas.ProcessBase(
            name="test.exe", parentprocessid=1, processid=2, architecture="64"
        )
        self.assertEqual(
            process_x64.architecture, "x64", "architecture was not parsed correctly"
        )
        process_x64 = schemas.ProcessBase(
            name="test.exe", parentprocessid=1, processid=2, architecture=" "
        )
        self.assertEqual(
            process_x64.architecture, "x32", "architecture was not parsed correctly"
        )
