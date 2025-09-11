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

from harbinger import models


import unittest


class TestMythicC2(unittest.TestCase):
    def test_db_models(self):
        test_text = "\x00 test test \x00"
        test_text_fixed = test_text.replace("\x00", "")
        test = models.C2Output(response_text=test_text)
        self.assertEqual(test.response_text, test_text_fixed)

        test = models.C2Task()
        test.command_name = test_text
        self.assertEqual(test.command_name, test_text_fixed)

        models.C2Output(response_text=None)
