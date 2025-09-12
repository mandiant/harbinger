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

import logging
import os
import sys
import unittest
from pathlib import Path

from alembic import command
from alembic.config import Config
from testcontainers.core.utils import inside_container
from testcontainers.postgres import PostgresContainer

from harbinger.config import get_settings

here = Path(os.path.dirname(os.path.abspath(__file__)))


class FixedPostgresContainer(PostgresContainer):
    def get_container_host_ip(self) -> str:
        if inside_container() and Path("/run/docker.sock").exists():
            return self.get_docker_client().gateway_ip(self._container.id)
        return super().get_container_host_ip()


def enable_logger():
    logger = logging.getLogger("alembic")
    logger.setLevel(logging.INFO)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)


class TestMigrations(unittest.TestCase):
    def test_migrations(self):
        with FixedPostgresContainer("postgres:14", driver="asyncpg") as postgres:
            psql_url = postgres.get_connection_url()
            os.environ["PG_DSN"] = psql_url
            os.environ["REDIS_DSN"] = "test"
            os.environ["MINIO_ACCESS_KEY"] = "test"
            os.environ["MINIO_SECRET_KEY"] = "test"
            os.environ["MINIO_HOST"] = "localhost"
            os.environ["MINIO_DEFAULT_BUCKET"] = "test"
            os.environ["TEMPORAL_HOST"] = "localhost"
            enable_logger()
            logger = logging.getLogger()
            get_settings.cache_clear()
            alembic_cfg = Config()
            alembic_cfg.set_main_option("script_location", str(here / ".." / "alembic"))
            alembic_cfg.set_main_option("sqlalchemy.url", psql_url)
            command.upgrade(alembic_cfg, "head")
            logger.info("Successfully migrated the database.")
            command.downgrade(alembic_cfg, "base")
            logger.info("Successfully downgraded the database.")
