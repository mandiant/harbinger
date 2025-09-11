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

import anyio
import asyncio
import traceback
import structlog

from aiosmb.commons.connection.factory import SMBConnectionFactory
from aiosmb.commons.interfaces.directory import SMBDirectory
from harbinger.database.database import SessionLocal
from harbinger import crud
from harbinger import schemas
from asyauth.common.credentials import UniCredential
from aiosmb.commons.connection.target import SMBTarget, SMBConnectionDialect
from asysocks.unicomm.common.proxy import UniProxyTarget
from alive_progress import alive_bar
from anyio.abc import TaskGroup


class ShareEnum:
    def __init__(
        self,
        proxy: UniProxyTarget,
        credential: UniCredential,
        tg: TaskGroup,
        smbv3: bool = False,
    ) -> None:
        self.logger = structlog.get_logger()
        self.proxy = proxy
        self.credential = credential
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.bar = lambda *args: None
        self.tg = tg
        self.smbv3 = smbv3

    async def worker(self, name: str, depth: int) -> None:
        while True:
            share_id = await self.queue.get()
            try:
                await self.list_share_folders(name, share_id, depth)
            except Exception as e:
                traceback.print_exc()
                self.logger.info(f"{name} encountered exception {type(e)}")
            finally:
                self.queue.task_done()
                self.bar()

    async def root_worker(self, name: str):
        while True:
            share_id = await self.queue.get()
            try:
                await self.list_share_root(name, share_id)
            except Exception as e:
                self.logger.info(f"{name} encountered exception {type(e)}")
                traceback.print_exc()
            finally:
                self.bar()
                self.queue.task_done()

    async def run_root(self, workers: int = 5, max_number: int = 0):
        for i in range(workers):
            self.tg.start_soon(self.root_worker, f"worker-{i}")

        async with SessionLocal() as session:
            entries = [
                entry
                for entry in await crud.indexer_list_shares(
                    session,
                    max_shares=max_number,
                    not_label_ids=[
                        "3f061979-055d-473f-ba15-d7b508f0ba83",
                        "851853d0-e540-4185-b46e-cf2e0cc63aa8",
                    ],
                )
            ]

            with alive_bar(len(entries), enrich_print=False) as bar:
                self.bar = bar
                for entry in entries:
                    self.queue.put_nowait(str(entry.id))
                self.logger.info(
                    f"Enumerating the root shares of {len(entries)} shares"
                )
                await self.queue.join()

        self.tg.cancel_scope.cancel()

    async def run(
        self, depth: int, workers: int = 5, max_number: int = 0, search: str = ""
    ):
        for i in range(workers):
            self.tg.start_soon(self.worker, f"worker-{i}", depth)

        async with SessionLocal() as session:
            entries = [
                entry
                for entry in await crud.indexer_list_shares_filtered(
                    session,
                    max_shares=max_number,
                    not_label_ids=[
                        "3f061979-055d-473f-ba15-d7b508f0ba83",
                    ],
                    file_type="dir",
                    indexed=False,
                    depth=depth,
                    search=search,
                )
            ]

            with alive_bar(len(entries), enrich_print=False) as bar:
                self.bar = bar
                for entry in entries:
                    self.queue.put_nowait(entry)
                self.logger.info(f"Enumerating {len(entries)} shares")
                await self.queue.join()

            self.logger.info("Done!")
            self.tg.cancel_scope.cancel()

    async def list_share_folders(self, name: str, share_id: str, depth: int):
        async with SessionLocal() as session:
            share = await crud.get_share(share_id)
            if not share:
                return 0

            files = [
                file
                for file in await crud.list_share_files(
                    session, share_id, depth, type="dir", indexed=False
                )
            ]

            if not files:
                return

            hostname = share.unc_path.split("\\")[2]
            self.logger.info(
                f"[{name}] Listing {len(files)} folders on {share.unc_path}"
            )
            target = SMBTarget(
                hostname=hostname, proxies=[self.proxy] if self.proxy else []
            )
            if self.smbv3:
                target.update_dialect(SMBConnectionDialect.SMB3)
            url = SMBConnectionFactory(self.credential, target)

            try:
                connection = url.get_connection()
                _, err = await connection.login()
                if err is not None:
                    self.logger.warning(f"Error connecting: {err}")
                    return
            except Exception as e:
                self.logger.error(f"Exception while connecting: {e}")
                return

            total_count = 0

            for parent_file in files:
                self.logger.debug(f"listing {parent_file.unc_path}")
                directory = SMBDirectory.from_uncpath(parent_file.unc_path)
                count = 0
                with anyio.fail_after(120):
                    try:
                        async for file, file_type, err in directory.list_gen(
                            connection
                        ):
                            if file.name:
                                await crud.create_share_file(
                                    session,
                                    schemas.ShareFileCreate(
                                        type=file_type,
                                        share_id=share_id,
                                        parent_id=parent_file.id,
                                        size=file.allocation_size,  # type: ignore
                                        name=file.name,
                                        depth=parent_file.depth + 1,
                                        last_accessed=file.last_access_time,
                                        last_modified=file.last_write_time,
                                        created=file.creation_time,
                                        unc_path=file.unc_path,
                                    ),
                                )
                                count += 1
                            if count > 1000:
                                self.logger.warning(
                                    f"Large fileshare (>1000) for speed sake going to skip the rest of {parent_file.unc_path}"
                                )
                                break
                            if count % 200 == 0:
                                await session.commit()
                        parent_file.indexed = True
                    except TimeoutError:
                        await session.rollback()
                        parent_file.indexed = False
                    except Exception:
                        await session.rollback()
                        parent_file.indexed = False
                total_count += count
                session.add(parent_file)
                await session.commit()

            await session.commit()
            await connection.disconnect()
            self.logger.info(f"found {total_count} files on {parent_file.unc_path}")

    async def list_share_root(self, name: str, share_id: str) -> int:
        async with SessionLocal() as session:
            share = await crud.get_share(share_id)
            if not share:
                return 0
            hostname = share.unc_path.split("\\")[2]

            self.logger.info(f"[{name}] Listing {share.unc_path} on {hostname}")

            target = SMBTarget(
                hostname=hostname, proxies=[self.proxy] if self.proxy else []
            )
            if self.smbv3:
                target.update_dialect(SMBConnectionDialect.SMB3)
            url = SMBConnectionFactory(self.credential, target)

            try:
                connection = url.get_connection()
                _, err = await connection.login()
                if err is not None:
                    return 0
            except Exception:
                return 0

            directory = SMBDirectory.from_uncpath(share.unc_path)
            count = 0
            try:
                async for file, file_type, err in directory.list_gen(connection):
                    if file.name:
                        await crud.create_share_file(
                            session,
                            schemas.ShareFileCreate(
                                type=file_type,
                                share_id=share_id,
                                parent_id=None,
                                size=file.allocation_size,  # type: ignore
                                name=file.name,
                                depth=0,
                                last_accessed=file.last_access_time,
                                last_modified=file.last_write_time,
                                created=file.creation_time,
                                unc_path=file.unc_path,
                            ),
                        )
                        count += 1
                        if count > 1000:
                            self.logger.warning(
                                f"Large fileshare (>1000) for speed sake going to skip the rest of {share.unc_path}"
                            )
                            break
                        if count % 200 == 0:
                            await session.commit()

                await session.commit()
                if count:
                    self.logger.info(
                        f"[{name}] found {count} files on {share.unc_path}"
                    )
            except Exception:
                pass
            finally:
                await connection.disconnect()

            # Label this share as enumerated root.
            await crud.create_label_item(
                session,
                schemas.LabeledItemCreate(
                    label_id="851853d0-e540-4185-b46e-cf2e0cc63aa8", share_id=share_id
                ),
            )
            return count
