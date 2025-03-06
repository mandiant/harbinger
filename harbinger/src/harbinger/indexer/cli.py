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

from harbinger.worker.client import get_client
from pydantic import UUID4
import click
import typing
from harbinger.indexer.list_shares import ListShares
from harbinger.indexer.list_files import ShareEnum
from harbinger.indexer.download_files import Downloader
from harbinger.indexer.upload_file import Uploader
from harbinger.database import crud
import structlog
import anyio
from asyauth.common.credentials import NTLMCredential
from asyauth.common.credentials.kerberos import KerberosCredential
from asysocks.unicomm.common.proxy import UniProxyTarget, UniProxyProto
from asyauth.common.constants import asyauthSecret
from harbinger.database.database import SessionLocal
from asysocks.unicomm.common.target import UniTarget, UniProto
from harbinger.files.client import download_file
from harbinger.database.redis_pool import redis

from functools import wraps

from dataclasses import dataclass
import signal


@dataclass
class ProxyCredentials:
    username: str
    password: str


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return anyio.run(f, *args, **kwargs)

    return wrapper


logger = structlog.get_logger()


@click.group()
def cli() -> None:
    pass


async def load_credential(
    credential_id: str | UUID4, dc_ip: str = ""
) -> NTLMCredential | KerberosCredential | None:
    async with SessionLocal() as session:
        cred_db = await crud.get_credential(session, credential_id)
        if not cred_db:
            return None
        if cred_db.kerberos:
            target = UniTarget(
                dc_ip=dc_ip, ip="", port=445, protocol=UniProto.CLIENT_TCP
            )
            return KerberosCredential(
                stype=asyauthSecret.CCACHEB64,
                secret=cred_db.kerberos.ccache,
                username=cred_db.username,
                domain=cred_db.domain.long_name,
                target=target,
            )
        else:
            return NTLMCredential(
                secret=cred_db.password.password or cred_db.password.nt,
                username=cred_db.username,
                stype=(
                    asyauthSecret.PASSWORD
                    if cred_db.password.password
                    else asyauthSecret.NT
                ),
                domain=cred_db.domain.short_name,
            )


async def load_proxy(proxy_id: str | UUID4) -> UniProxyTarget | None:
    async with SessionLocal() as session:
        proxy_db = await crud.get_proxy(session, proxy_id=proxy_id)
        if not proxy_db:
            return None
        proxy = UniProxyTarget()
        if proxy_db.username or proxy_db.password:
            proxy.credential = ProxyCredentials(proxy_db.username, proxy_db.password)  # type: ignore
        if proxy_db.type == "socks5":
            proxy.protocol = UniProxyProto.CLIENT_SOCKS5_TCP
        elif proxy_db.type == "socks4":
            proxy.protocol = UniProxyProto.CLIENT_SOCKS4
        proxy.server_port = proxy_db.port
        proxy.server_ip = proxy_db.host
        return proxy


async def get_file(file_id: str | UUID4) -> bytes | None:
    async with SessionLocal() as session:
        file_db = await crud.get_file(session, file_id)
        if not file_db:
            return None
        return await download_file(file_db.path, file_db.bucket)


@cli.command()
@click.argument("hosts", type=click.File("r"))
@click.option("--workers", type=int, default=5)
@click.option("--proxy", type=str, required=True)
@click.option("--credential", type=str, required=True)
@click.option("--dc-ip", type=str)
@click.option("--max-hosts", type=int, default=100000000)
@click.option("--sleep", type=int, default=0)
@click.option("--smbv3", is_flag=True, show_default=True, default=False, help="Force smbv3")
def list_shares(
    hosts: typing.IO, workers: int, proxy: str, credential: str, dc_ip: str, max_hosts: int, sleep: int, smbv3: bool = False,
) -> None:
    anyio.run(list_sharesa, hosts, workers, proxy, credential, dc_ip, max_hosts, sleep, smbv3)


async def list_sharesa(
    hosts: typing.IO, workers: int, proxy_id: str, credential_id: str, dc_ip: str, max_hosts: int, sleep: int, smbv3: bool,
) -> None:
    data = [h.strip() for h in hosts.readlines()]
    logger.info(f"Listing shares on {len(data)} hosts")

    proxy = await load_proxy(proxy_id=proxy_id)
    if not proxy:
        logger.warning("Could not find the proxy with that id...")
        return

    credential = await load_credential(credential_id=credential_id, dc_ip=dc_ip)
    if not credential:
        logger.warning("Could not find the credential with that id...")
        return

    try:
        async with anyio.create_task_group() as tg:
            shares = ListShares(proxy=proxy, credential=credential, tg=tg, smbv3=smbv3)
            tg.start_soon(shares.run, data, workers, max_hosts, sleep)

            with anyio.open_signal_receiver(signal.SIGTERM, signal.SIGINT) as signals:
                async for signum in signals:
                    tg.cancel_scope.cancel()
    finally:
        await redis.aclose()


@cli.command()
@click.option("--workers", type=int, default=5)
@click.option("--proxy", type=str, required=True)
@click.option("--credential", type=str, required=True)
@click.option("--max", type=int, default=0, help="Max shares to enumerate")
@click.option("--dc-ip", type=str)
@click.option("--smbv3", is_flag=True, show_default=True, default=False, help="Force smbv3")
def list_root_shares(workers: int, proxy: str, credential: str, max: int = 0, dc_ip: str = "", smbv3: bool = False) -> None:
    anyio.run(list_root_sharesa, workers, max, proxy, credential, dc_ip, smbv3)


async def list_root_sharesa(
    workers: int, max: int, proxy_id: str, credential_id: str, dc_ip, smbv3: bool = False
) -> None:
    proxy = await load_proxy(proxy_id=proxy_id)
    if not proxy:
        logger.warning("Could not find the proxy with that id...")
        return

    credential = await load_credential(credential_id=credential_id, dc_ip=dc_ip)
    if not credential:
        logger.warning("Could not find the credential with that id...")
        return

    try:
        async with anyio.create_task_group() as tg:
            enum = ShareEnum(proxy, credential, tg, smbv3)
            await enum.run_root(workers=workers, max_number=max)
    finally:
        await redis.aclose()

@cli.command()
@click.argument("depth", type=int)
@click.option("--workers", type=int, default=5)
@click.option("--proxy", type=str, required=True)
@click.option("--credential", type=str, required=True)
@click.option("--max", type=int, default=0, help="Max shares to enumerate")
@click.option("--dc-ip", type=str, default="")
@click.option("--search", type=str, default="")
@click.option("--smbv3", is_flag=True, show_default=True, default=False, help="Force smbv3")
def list_shares_depth(
    depth: int, workers: int, proxy: str, credential: str, max: int = 0, dc_ip: str = "", search: str = "", smbv3: bool = False
) -> None:
    anyio.run(list_shares_deptha, depth, workers, max, proxy, credential, dc_ip, search, smbv3)


async def list_shares_deptha(
    depth: int, workers: int, max: int, proxy_id: str, credential_id: str, dc_ip: str = "", search: str = "", smbv3: bool = False
) -> None:
    proxy = await load_proxy(proxy_id=proxy_id)
    if not proxy:
        logger.warning("Could not find the proxy with that id...")
        return

    credential = await load_credential(credential_id=credential_id, dc_ip=dc_ip)
    if not credential:
        logger.warning("Could not find the credential with that id...")
        return

    try:
        async with anyio.create_task_group() as tg:
            enum = ShareEnum(proxy, credential, tg, smbv3)
            await enum.run(depth=depth, workers=workers, max_number=max, search=search)
    finally:
        await redis.aclose()

@cli.command()
@click.argument("search", type=str)
@click.option("--workers", type=int, default=5)
@click.option("--proxy", type=str, required=True)
@click.option("--credential", type=str, required=True)
@click.option("--max", type=int, default=0, help="Max shares to enumerate")
@click.option("--dc-ip", type=str, default="")
@click.option("--smbv3", is_flag=True, show_default=True, default=False, help="Force smbv3")
def download(search, workers: int, proxy: str, credential: str, max: int = 0, dc_ip: str = "", smbv3: bool = False) -> None:
    anyio.run(downloada, search, workers, proxy, credential, max, dc_ip, smbv3)


async def downloada(
    search, workers: int, proxy_id: str, credential_id: str, max: int = 0, dc_ip: str = "", smbv3: bool = False
) -> None:
    proxy = await load_proxy(proxy_id=proxy_id)
    if not proxy:
        logger.warning("Could not find the proxy with that id...")
        return

    credential = await load_credential(credential_id=credential_id, dc_ip=dc_ip)
    if not credential:
        logger.warning("Could not find the credential with that id...")
        return

    client = await get_client()
    try:
        async with anyio.create_task_group() as tg:
            downloader = Downloader(proxy, credential, tg, client, smbv3)
            await downloader.run(search, workers=workers, max_number=max)
    finally:
        await redis.aclose()

@cli.command()
@click.option("--proxy", type=str, required=True)
@click.option("--credential", type=str, required=True)
@click.option("--file", type=str, required=True)
@click.option("--unc", type=str, required=True)
@click.option("--dc-ip", type=str, default="")
@click.option("--smbv3", is_flag=True, show_default=True, default=False, help="Force smbv3")
def upload(proxy: str, credential: str, file: str, unc: str, dc_ip: str = "", smbv3: bool = False) -> None:
    anyio.run(uploada, proxy, credential, file, unc, dc_ip, smbv3)

async def uploada(
    proxy_id: str, credential_id: str, file_id: str, unc: str, dc_ip: str = "", smbv3: bool = False
) -> None:
    proxy = await load_proxy(proxy_id=proxy_id)
    if not proxy:
        logger.warning("Could not find the proxy with that id...")
        return

    credential = await load_credential(credential_id=credential_id, dc_ip=dc_ip)
    if not credential:
        logger.warning("Could not find the credential with that id...")
        return

    data = await get_file(file_id)
    if not data:
        logger.error("Could not retrieve the file of that id.")
        return

    try:
        uploader = Uploader(proxy, credential, smbv3)
        await uploader.upload_file(data=data, unc_path=unc)
    finally:
        await redis.aclose()

if __name__ == "__main__":
    cli()
