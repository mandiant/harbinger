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

import traceback
import humanize

import structlog
from aiosmb.commons.connection.factory import SMBConnectionFactory
from aiosmb.commons.connection.target import SMBTarget, SMBConnectionDialect

from aiosmb.commons.interfaces.file import SMBFile
from alive_progress import alive_bar
from asyauth.common.credentials import UniCredential
from asysocks.unicomm.common.proxy import UniProxyTarget


from harbinger.config import get_settings

settings = get_settings()


class Uploader:

    def __init__(
        self,
        proxy: UniProxyTarget,
        credential: UniCredential,
        smbv3: bool = False,
    ) -> None:
        self.logger = structlog.get_logger()
        self.proxy = proxy
        self.credential = credential
        self.smbv3: bool = smbv3

    async def upload_file(self, unc_path: str, data: bytes) -> None:
        hostname = [entry for entry in unc_path.split("\\") if entry][0]
        self.logger.info(f"[{hostname}] Uploading {humanize.naturalsize(len(data))} bytes to {unc_path}")
        target = SMBTarget(hostname=hostname, proxies=[self.proxy] if self.proxy else [])
        if self.smbv3:
            target.update_dialect(SMBConnectionDialect.SMB3)
        url = SMBConnectionFactory(self.credential, target)
        try:
            connection = url.get_connection()
            _, err = await connection.login()
            if err is not None:
                self.logger.error(f"Error during connection: {err}")
                return
        except Exception as e:
            self.logger.error(f"Exception during connection: {str(e)}")
            return
        try:
            smbfile = SMBFile.from_uncpath(unc_path)
            _, err = await smbfile.open(connection, 'w')
            if err != None:
                self.logger.error(err)
                return
            with alive_bar(len(data)) as bar:
                step = 100000
                for i in range(0, len(data), step):
                    total_writen, err = await smbfile.write(data[i:i+step])
                    bar(total_writen)
                await smbfile.close()
        except Exception as e:
            self.logger.error(f"Exception: {e}")
            traceback.print_exc()
        finally:
            await connection.disconnect()
        return
