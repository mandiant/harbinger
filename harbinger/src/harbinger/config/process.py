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

import pathlib
from typing import Dict
import yaml
from harbinger.database import schemas


def get_process_mapping() -> Dict[str, str]:
    result = dict()
    base = pathlib.Path(__file__).parent.resolve() / "process"
    files = [x for x in base.iterdir()]
    for file in files:
        with open(file, "r") as f:
            yaml_data = f.read()
        for entry in yaml.safe_load_all(yaml_data):
            entry = schemas.ProcessMapping(**entry)
            for process in entry.processes:
                result[process] = entry.tag_id
    return result
