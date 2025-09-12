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

# Python script that will apply the migrations up to head
import logging
import os
import socket
import sys
from pathlib import Path

import backoff
import click
from alembic import command
from alembic.config import Config

from harbinger.config import get_settings

settings = get_settings()

here = Path(os.path.dirname(os.path.abspath(__file__)))


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


@backoff.on_exception(backoff.expo, (socket.gaierror), max_time=300)
def run_migrations() -> None:
    enable_logger()
    logger = logging.getLogger()
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(here / ".." / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.pg_dsn)
    command.upgrade(alembic_cfg, "head")
    logger.info("Successfully migrated the database.")


@click.command()
@click.option("--message", "-m")
def auto_revision(message: str) -> None:
    enable_logger()
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(here / ".." / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.pg_dsn)
    command.revision(alembic_cfg, message, True)


@click.command()
@click.argument("revision")
def downgrade(revision: str) -> None:
    enable_logger()
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", str(here / ".." / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.pg_dsn)
    command.downgrade(alembic_cfg, revision)
