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

import anyio
import humanize
import structlog
from aiosmb.commons.connection.factory import SMBConnectionFactory
from aiosmb.commons.connection.target import SMBConnectionDialect, SMBTarget
from aiosmb.commons.interfaces.file import SMBFile
from alive_progress import alive_bar
from anyio.abc import TaskGroup
from asyauth.common.credentials import UniCredential
from asysocks.unicomm.common.proxy import UniProxyTarget
from temporalio.client import Client

from harbinger import crud, models, schemas
from harbinger.config import constants, get_settings
from harbinger.database.database import SessionLocal
from harbinger.files.client import FileUploader
from harbinger.worker.workflows import ParseFile

settings = get_settings()


class Downloader:
    def __init__(
        self,
        proxy: UniProxyTarget,
        credential: UniCredential,
        tg: TaskGroup,
        client: Client,
        smbv3: bool = False,
    ) -> None:
        self.logger = structlog.get_logger()
        self.proxy = proxy
        self.credential = credential
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.bar = lambda *args: None
        self.tg = tg
        self.client = client
        self.smbv3: bool = smbv3

    async def process_file(self, file_id: str) -> None:
        await self.client.start_workflow(
            ParseFile.run,
            file_id,
            id=str(uuid.uuid4()),
            task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
        )

    async def download_worker(self, name: str):
        while True:
            async with SessionLocal() as session:
                try:
                    file_id = await self.queue.get()
                    file = await crud.get_share_file(file_id)

                    if not file:
                        self.logger.warning(
                            f"Unable to find the file with id: {file_id}",
                        )
                        return

                    path = os.path.join("share_indexer", f"{file.id}_{file.name}")
                    new_file_id: None | uuid.UUID = None
                    downloaded = False
                    try:
                        with anyio.fail_after(120):
                            downloaded = await self.download_file(path, file)

                        if downloaded:
                            file_db = await crud.add_file(
                                session,
                                filename=file.name,
                                bucket=settings.minio_default_bucket,
                                path=path,
                            )

                            await crud.create_label_item(
                                session,
                                schemas.LabeledItemCreate(
                                    label_id="ceccea96-9c5a-434e-ad55-e15d7c63f6ac",
                                    file_id=file_db.id,
                                ),
                            )
                            new_file_id = file_db.id
                            await self.process_file(str(new_file_id))

                    except TimeoutError:
                        self.logger.info(f"TimeOut during download of {path}")
                        downloaded = False

                    await crud.update_share_file(
                        session,
                        file.id,
                        schemas.ShareFileUpdate(
                            downloaded=downloaded,
                            file_id=new_file_id,
                        ),
                    )
                    await session.commit()

                except Exception as e:
                    self.logger.info(f"{name} encountered exception {type(e)}")
                    self.logger.info(e)
                    import traceback

                    traceback.print_exc()

                finally:
                    self.queue.task_done()
                    self.bar()

    async def run(self, search: str, workers: int = 5, max_number: int = 0):
        for i in range(workers):
            self.tg.start_soon(self.download_worker, f"worker-{i}")

        async with SessionLocal() as session:
            files = await crud.list_share_files(
                session,
                type="file",
                search=search,
                max_size=100000000,
                downloaded=False,
                limit=max_number,
            )
            total_size = 0
            entries = list(files)
            with alive_bar(len(entries), enrich_print=False) as bar:
                self.bar = bar
                for entry in entries:
                    total_size += entry.size
                    self.queue.put_nowait(str(entry.id))
                self.logger.info(
                    f"Queued {len(entries)} files totalling {humanize.naturalsize(total_size, binary=True)} in size",
                )
                await self.queue.join()
        self.logger.info("Done!")
        self.tg.cancel_scope.cancel()

    async def download_file(
        self,
        key: str,
        file: models.ShareFile | schemas.ShareFile,
    ) -> bool:
        if not file.unc_path:
            self.logger.error("Unc path not set")
            return False
        hostname = file.unc_path.split("\\")[2]
        self.logger.info(f"Downloading {file.name} from {hostname} to {key}")
        target = SMBTarget(
            hostname=hostname,
            proxies=[self.proxy] if self.proxy else [],
        )
        if self.smbv3:
            target.update_dialect(SMBConnectionDialect.SMB3)
        url = SMBConnectionFactory(self.credential, target)

        try:
            connection = url.get_connection()
            _, err = await connection.login()
            if err is not None:
                self.logger.error(f"Error during downloading file: {err}")
                return False
        except Exception as e:
            self.logger.exception(f"Error during downloading file: {e}")
            return False

        try:
            smbfile = SMBFile.from_uncpath(file.unc_path)
            _, err = await smbfile.open(connection, "r")
            if err is not None:
                self.logger.error(f"Error during downloading file: {err}")
                return False

            async with FileUploader(key, settings.minio_default_bucket) as f:
                async for data, err in smbfile.read_chunked():
                    if err is not None:
                        self.logger.error(f"Error during downloading file: {err}")
                        raise err
                    if data is None:
                        break
                    await f.upload(data)

        except Exception as e:
            self.logger.exception(f"Exception during download of file: {type(e)}")
            return False
        finally:
            await connection.disconnect()
        return True
