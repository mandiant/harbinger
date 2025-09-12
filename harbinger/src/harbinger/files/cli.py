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
import os
import uuid
from pathlib import Path

import click

from harbinger import crud
from harbinger.config import constants, get_settings
from harbinger.database.database import SessionLocal
from harbinger.database.redis_pool import redis
from harbinger.files.client import download_file, upload_file
from harbinger.worker.client import get_client
from harbinger.worker.workflows import ParseFile


def is_uuid(uuid_str: str):
    try:
        uuid.UUID(uuid_str)
        return True
    except ValueError:
        return False


settings = get_settings()


async def upload_single_file(path: Path, socks_job_id: str, filetype: str):
    with open(path, "rb") as f:
        data = f.read()

    filename = os.path.basename(str(path))
    async with SessionLocal() as db:
        file_db = await crud.add_file(
            db,
            filename=filename,
            bucket=settings.minio_default_bucket,
            path="",
            job_id=socks_job_id or None,
            filetype=filetype,
        )
        file_id = file_db.id
        path_str = os.path.join("harbinger", f"{file_id}_{filename}")
        await crud.update_file_path(db, file_id, path_str)
        await upload_file(path_str, data)
        client = await get_client()
        await client.start_workflow(
            ParseFile.run,
            str(file_id),
            id=str(uuid.uuid4()),
            task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
        )


async def upload_main(
    path: str,
    exclude: list[str] | None = None,
    socks_job_id: str = "",
    filetype: str = "",
) -> None:
    if exclude is None:
        exclude = []
    p = Path(path)
    to_upload = []
    if p.is_dir():
        for x in p.iterdir():
            y = Path(x)
            if y.is_file() and y.name not in exclude:
                to_upload.append(y)
    elif p.is_file():
        to_upload.append(p)
    click.echo(f"Uploading {len(to_upload)} files to Harbinger")

    for u in to_upload:
        await upload_single_file(u, socks_job_id, filetype)
        click.echo(f"Uploaded {u!s}")
    await redis.aclose()


async def download_main(files: list[str], destination: str, bucket: str) -> None:
    dest = Path(destination)
    click.echo(f"Downloading {len(files)} file(s) to {destination}")
    for file in files:
        file_path = file
        filename = file
        if is_uuid(file):
            file_db = await crud.get_file(file)
            if file_db:
                file_path = file_db.path
                filename = os.path.basename(file_db.filename)
            else:
                click.echo(f"File with guid {file} not found, skipping.")
                continue
        else:
            file_path = file
            filename = os.path.basename(file)

        data = await download_file(file_path, bucket)
        with open(dest / filename, "wb") as f:
            f.write(data)
        click.echo(f"Written {len(data)} bytes to {dest / filename}")


@click.group()
def cli():
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--exclude", "-e", multiple=True)
@click.option("--socks-job-id", type=str, default="")
@click.option("--filetype", type=str, default="")
def upload(path: str, exclude: tuple[str], socks_job_id: str, filetype: str):
    asyncio.run(upload_main(path, list(exclude), socks_job_id, filetype))


@cli.command()
@click.argument("files", nargs=-1)
@click.option("--destination", "-d", type=click.Path(exists=True), default=os.getcwd())
@click.option("--bucket", "-b", type=str, default=settings.minio_default_bucket)
def download(files: tuple[str], destination: str, bucket: str):
    asyncio.run(download_main(list(files), destination, bucket))
