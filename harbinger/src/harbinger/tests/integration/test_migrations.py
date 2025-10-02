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
from pathlib import Path

from alembic import command
from alembic.config import Config

# Calculate the correct path to the alembic directory from the test file's location.
# The test file is in tests/integration/, so we need to go up two levels.
here = Path(os.path.dirname(os.path.abspath(__file__)))
alembic_script_location = str(here / ".." / ".." / "alembic")


def enable_logger():
    """Enable detailed logging for Alembic commands."""
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
    # Avoid adding duplicate handlers if the logger is already configured.
    if not root.handlers:
        root.addHandler(handler)


def test_migrations_downgrade(migrated_db):
    """
    Tests that the database can be successfully downgraded to base.

    The `migrated_db` fixture, defined in conftest.py, has already
    run the equivalent of `alembic upgrade head`. This test verifies
    that the migrations are reversible.
    """
    enable_logger()
    logger = logging.getLogger(__name__)

    pg_dsn = migrated_db
    # Alembic needs the synchronous DSN format.
    sync_psql_url = pg_dsn.replace("+asyncpg", "")

    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", alembic_script_location)
    alembic_cfg.set_main_option("sqlalchemy.url", sync_psql_url)

    logger.info("Attempting to downgrade the database to base...")
    command.downgrade(alembic_cfg, "base")
    logger.info("Successfully downgraded the database.")

    # To complete the cycle, we can upgrade again.
    logger.info("Attempting to upgrade the database back to head...")
    command.upgrade(alembic_cfg, "head")
    logger.info("Successfully upgraded the database back to head.")
