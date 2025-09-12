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
import traceback

import structlog
from aiosmb.commons.connection.factory import SMBConnectionFactory
from aiosmb.commons.connection.target import SMBConnectionDialect, SMBTarget
from aiosmb.commons.interfaces.machine import SMBMachine
from alive_progress import alive_bar
from anyio.abc import TaskGroup
from asyauth.common.credentials import UniCredential
from asysocks.unicomm.common.proxy import UniProxyTarget

from harbinger import crud, schemas
from harbinger.database.database import SessionLocal


class ListShares:
    def __init__(
        self,
        proxy: UniProxyTarget | None,
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

    async def worker(self, name: str):
        while True:
            hostname = await self.queue.get()
            self.logger.info(f"{name} listing shares on {hostname}")
            try:
                count = await self.list_shares_on_host(hostname)
                self.logger.info(f"{name} found {count} shares on {hostname}")
            except Exception as e:
                self.logger.exception(f"Exception {e}")
            finally:
                self.queue.task_done()
                self.bar()

    async def run(
        self,
        hosts: list,
        workers: int,
        max_hosts: int = 100000000,
        wait: int = 0,
    ) -> None:
        for i in range(workers):
            self.tg.start_soon(self.worker, f"worker-{i}")

        count = 0
        with alive_bar(len(hosts), enrich_print=False) as bar:
            self.bar = bar
            for host in hosts:
                self.queue.put_nowait(host)
                count += 1
                if count == max_hosts:
                    count = 0
                    self.logger.info(f"Max hosts reached, sleeping for {wait} seconds")
                    await asyncio.sleep(wait)

            await self.queue.join()
        self.logger.info("Completed enumeration!")
        self.tg.cancel_scope.cancel()

    async def list_shares_on_host(self, hostname: str) -> int:
        target = SMBTarget(
            hostname=hostname,
            proxies=[self.proxy] if self.proxy else [],
        )
        if self.smbv3:
            target.update_dialect(SMBConnectionDialect.SMB3)

        url = SMBConnectionFactory(self.credential, target)
        async with SessionLocal() as session:
            _, host = await crud.get_or_create_host(session, hostname)
            host_id = host.id
        try:
            connection = url.get_connection()
            _, err = await connection.login()
            if err is not None:
                self.logger.debug(f"Error during connection: {err}")
                return 0
        except Exception as e:
            self.logger.debug(f"Exception during connection: {e!s}")
            return 0

        machine = SMBMachine(connection)
        count = 0
        try:
            async with SessionLocal() as session:
                async for share, err in machine.list_shares():
                    if err is not None:
                        self.logger.debug(f"Error during listing shares: {err}")
                        continue
                    created, _ = await crud.get_or_create_share(
                        session,
                        schemas.ShareCreate(
                            name=share.name,
                            host_id=host_id,
                            unc_path=share.unc_path,
                            type=share.type,
                            remark=share.remark,
                        ),
                    )  # type: ignore
                    if created:
                        count += 1
                        self.logger.info(
                            f"Created share with name: {share.name} and unc_path: {share.unc_path}",
                        )
                    else:
                        self.logger.debug(
                            f"Share with name: {share.name} and unc_path: {share.unc_path} already exists",
                        )
                await session.commit()
        except Exception as e:
            self.logger.exception(f"Exception: {e}")
            traceback.print_exc()
        finally:
            await connection.disconnect()
        return count
