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

from harbinger import schemas
from harbinger.config.process import get_process_mapping


def test_get_process_mapping():
    """
    Tests that the process mapping can be loaded and is not empty.
    """
    result = get_process_mapping()
    assert len(result) > 0


def test_process_base_schema():
    """
    Tests the architecture parsing in the ProcessBase schema.
    """
    # Test x64 architecture
    process_x64 = schemas.ProcessBase(
        name="test.exe",
        parentprocessid=1,
        processid=2,
        architecture="64",
    )
    assert process_x64.architecture == "x64", "Architecture '64' was not parsed to 'x64'"

    # Test x32 (default) architecture
    process_x32 = schemas.ProcessBase(
        name="test.exe",
        parentprocessid=1,
        processid=2,
        architecture=" ",
    )
    assert process_x32.architecture == "x32", "Blank architecture was not parsed to 'x32'"
