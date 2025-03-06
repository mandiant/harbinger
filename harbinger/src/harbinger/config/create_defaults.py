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
from harbinger.database import crud, schemas
from harbinger.database.database import SessionLocal
from sqlalchemy.exc import IntegrityError
import zipfile
import os.path
import click
from harbinger.files.client import upload_file
from harbinger.config import get_settings
from harbinger.database.redis_pool import redis
from harbinger.worker.files.utils import process_harbinger_yaml


settings = get_settings()


async def create_all():
    async with SessionLocal() as db:
        for directory in ["connectors", "labels", "settings"]:
            base = pathlib.Path(__file__).parent.resolve() / directory
            print(f"Checking {base}")
            files = [x for x in base.iterdir()]
            for file in files:
                print(f"Processing {file}")
                with open(file, "r") as f:
                    yaml_data = f.read()
                    await process_harbinger_yaml(db, yaml_data)


async def acreate_defaults():
    try:
        await create_all()
    finally:
        await redis.aclose()


@click.command()
def create_defaults():
    asyncio.run(acreate_defaults())
