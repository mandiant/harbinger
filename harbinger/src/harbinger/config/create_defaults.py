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

import asyncio
import pathlib

import click
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger.config import get_settings
from harbinger.database.database import SessionLocal
from harbinger.database.redis_pool import redis
from harbinger.worker.files.utils import process_harbinger_yaml

settings = get_settings()
log = structlog.get_logger()


async def create_all(db: AsyncSession | None = None):
    log.info("Starting create_all")

    async def process_files(db_session: AsyncSession):
        for directory in ["connectors", "labels", "settings", "playbooks"]:
            base = pathlib.Path(__file__).parent.resolve() / directory
            log.info(f"Checking {base}")
            files = list(base.iterdir())
            for file in files:
                log.info(f"Processing {file}")
                with open(file) as f:
                    yaml_data = f.read()
                    await process_harbinger_yaml(db_session, yaml_data)

    if db:
        await process_files(db)
    else:
        async with SessionLocal() as db_session:
            await process_files(db_session)

    log.info("Finished create_all")


async def acreate_defaults():
    try:
        await create_all()
    finally:
        await redis.aclose()


@click.command()
def create_defaults():
    asyncio.run(acreate_defaults())
