# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from harbinger import models


def test_db_models_strip_null_bytes():
    """
    Tests that null bytes are correctly stripped from model fields.
    """
    test_text = "\x00 test test \x00"
    test_text_fixed = " test test "

    # Test C2Output model
    c2_output = models.C2Output(response_text=test_text)
    assert c2_output.response_text == test_text_fixed

    # Test C2Task model
    c2_task = models.C2Task()
    c2_task.command_name = test_text
    assert c2_task.command_name == test_text_fixed


def test_db_models_handle_none():
    """
    Tests that model fields can correctly be set to None without raising an error.
    """
    c2_output = models.C2Output(response_text=None)
    assert c2_output.response_text is None
