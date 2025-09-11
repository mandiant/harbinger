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

from functools import lru_cache
import socket

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    redis_dsn: str
    pg_dsn: str

    minio_access_key: str
    minio_secret_key: str
    minio_host: str
    minio_default_bucket: str

    neo4j_host: str = ""
    neo4j_user: str = ""
    neo4j_password: str = ""

    lifetime_seconds: int = 3600 * 24 * 7
    cookie_samesite: str = "strict"

    dev_mode: bool = False

    hostname: str = socket.gethostname()

    temporal_host: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    bofhound: str = "/opt/tools/bofhound_venv/bin/bofhound"

    trufflehog: str = "/opt/tools/trufflehog"

    noseyparker: str = "/opt/tools/noseyparker"

    gemini_model: str = "gemini/gemini-2.5-pro"

    gemini_enabled: bool = False


@lru_cache()
def get_settings():
    return Settings()  # type: ignore
