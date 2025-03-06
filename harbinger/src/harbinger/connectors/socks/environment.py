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

import os

TMATE_KEYS = [
    "TMATE_SERVER",
    "TMATE_PORT",
    "RSA_SIG",
    "ED25519_SIG",
]

SERVER_ENV = [
    "TEMPORAL_HOST",
    "HARBINGER_GRPC_HOST",
]


async def get_environment(env_keys: list[str]) -> list[str]:
    result = []
    for key in env_keys:
        value = os.environ.get(key)
        if value:
            result.append(f"{key}={value}")
    return result


async def get_environment_dict(env_keys: list[str]) -> dict[str, str]:
    result = {}
    for key in env_keys:
        value = os.environ.get(key)
        if value:
            result[key] = value
    return result
