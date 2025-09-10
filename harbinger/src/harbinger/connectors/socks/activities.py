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
from temporalio import activity
from harbinger.database import crud
from harbinger import schemas
import harbinger.proto.v1.messages_pb2 as messages_pb2
from harbinger.connectors.socks import schemas as socks_schemas
from harbinger.database.database import SessionLocal
import aiodocker
import shlex
from aiodocker.volumes import DockerVolume
import structlog
from harbinger.database.redis_pool import redis
from harbinger.config import get_settings
from harbinger.connectors.socks.environment import (
    get_environment,
    get_environment_dict,
    TMATE_KEYS,
    SERVER_ENV,
)
from aiodocker.containers import DockerContainer
import tarfile
import io
import uuid
import os
from harbinger.files.client import FileUploader, download_file
from base64 import b64decode


settings = get_settings()


log = structlog.get_logger()


@activity.defn
async def get_proxy_job(proxy_job_id: str) -> schemas.ProxyJob | None:
    proxy_job = await crud.get_proxy_job(proxy_job_id)
    if proxy_job:
        return schemas.ProxyJob.model_validate(proxy_job)
    return None


@activity.defn(name="update_proxy_job_status")
async def update_proxy_job_status(status: schemas.ProxyJob) -> None:
    log.info(f"Setting status for {status.id} to {status.status}")
    async with SessionLocal() as session:
        await crud.update_proxy_job_status(
            session, status.status, status.id, exit_code=status.exit_code or 0
        )
        step = await crud.get_chain_step_by_proxy_job_id(
            session,
            str(status.id),
        )
        if step:
            await crud.update_step_status(
                session, status=status.status or "", step_id=step.id
            )


async def save_output(job_id: str, output: str) -> None:
    output = output.replace("\x00", "")
    async with SessionLocal() as session:
        mes = schemas.ProxyJobOutputCreate(
            job_id=job_id,
            output=output,
        )
        await crud.create_proxy_job_output(session, mes)
        await redis.publish(
            f"proxy_job_stream_{job_id}",
            messages_pb2.Output(output=output).SerializeToString(),
        )


@activity.defn
async def save_output_activity(output: socks_schemas.Output) -> None:
    await save_output(output.job_id, output.output)


@activity.defn
async def save_files(files: socks_schemas.Files) -> None:
    async with SessionLocal() as session:
        for file in files.files:
            await crud.add_file(
                session,
                filename=file.filename,
                bucket=settings.minio_default_bucket,
                path=file.path,
                job_id=files.id or None,
                id=file.id or None,
            )


async def upload_bytes(
    container: DockerContainer, data: bytes, filename: str, location: str
):
    fh = io.BytesIO()
    dp = io.BytesIO(initial_bytes=data)
    with tarfile.open(fileobj=fh, mode="w:gz") as tar:
        info = tarfile.TarInfo(filename)
        info.size = len(data)
        tar.addfile(info, dp)
    await container.put_archive(location, fh.getvalue())


PROXYCHAINS_CONFIG = """
strict_chain
proxy_dns
remote_dns_subnet 224

tcp_read_time_out 100000000
tcp_connect_time_out 100000000

[ProxyList]
{PROXY_CONFIG}
"""

TMATE_CONFIG = """
set -g tmate-server-host {TMATE_SERVER}
set -g tmate-server-port {TMATE_PORT}
set -g tmate-server-rsa-fingerprint {RSA_SIG}
set -g tmate-server-ed25519-fingerprint {ED25519_SIG}
"""


@activity.defn
async def run_proxy_job(
    socks_task: socks_schemas.SocksTask,
) -> socks_schemas.SocksTaskResult:
    output: list[str] = []
    result = socks_schemas.SocksTaskResult(
        id=socks_task.id, status=schemas.Status.created
    )
    docker = aiodocker.Docker()
    try:
        environment = await get_environment(TMATE_KEYS)
        environment_dict = await get_environment_dict(TMATE_KEYS)

        if socks_task.proxy:
            environment.append(f"PROXY_CONFIG={socks_task.proxy.to_str()}")
        if socks_task.credential and socks_task.credential.kerberos:
            environment.append(f"KRB5CCNAME={socks_task.credential.username}.ccache")
        if socks_task.env:
            environment.extend(socks_task.env.split(","))

        command = []
        if socks_task.tmate:
            command.extend(
                ["/usr/bin/tmate", "-F", "new-session", "-x", "160", "-y", "48"]
            )
        if socks_task.proxychains:
            command.append("proxychains")
        if socks_task.asciinema:
            command.extend(["asciinema", "rec", "output.cast", "-c"])
            command.append(
                f"{socks_task.command} {socks_task.arguments}".strip()
            )
        else:
            command.append(socks_task.command)
            command.extend(shlex.split(socks_task.arguments))

        log.info(f"Command for {socks_task.id}: {command}")
        config = {
            "Image": f"harbinger_proxy:latest",
            "Cmd": ["tail", "-f", "/dev/null"],
            "AttachStdin": False,
            "AttachStdout": True,
            "AttachStderr": True,
            "Tty": False,
            "OpenStdin": False,
            "Name": f"harbinger_socks_{socks_task.id}",
            "Env": environment,
            "HostConfig": {
                "NetworkMode": "harbinger",
            },
            "WorkingDir": "/workdir",
        }
        container = await docker.containers.create(
            config=config,
            name=f"harbinger_socks_{socks_task.id}",
        )
        await container.start()

        if socks_task.tmate:
            try:
                tmate_config = TMATE_CONFIG.format(**environment_dict).encode("utf-8")
                await upload_bytes(container, tmate_config, ".tmate.conf", "/home/user")
            except KeyError:
                log.warning("Unable to generate TMATE_CONFIG, unset keys in environment.")

        ignore_files = []
        for file in socks_task.files or []:
            file_data = await download_file(file.path, file.bucket)
            await upload_bytes(container, file_data, file.filename, "/workdir")
            ignore_files.append(file.filename)

        if socks_task.proxy:
            proxy_config = PROXYCHAINS_CONFIG.format(
                PROXY_CONFIG=socks_task.proxy.to_str()
            ).encode("utf-8")
            await upload_bytes(container, proxy_config, "proxychains4.conf", "/etc")

        if socks_task.credential and socks_task.credential.kerberos:
            credential_data = b64decode(socks_task.credential.kerberos.ccache)
            await upload_bytes(
                container,
                credential_data,
                f"{socks_task.credential.username}.ccache",
                "/workdir",
            )
            ignore_files.append(f"{socks_task.credential.username}.ccache")

        execution = await container.exec(command, stdout=True, stderr=True, tty=True)
        async with execution.start(detach=False) as stream:
            running = True
            while running:
                data = await stream.read_out()
                if not data:
                    break
                entry = data.data.decode("utf-8", errors="ignore").strip()
                for line in entry.splitlines():
                    if socks_task.tmate and "Session shell restarted" in line:
                        log.debug("Stopping!")
                        running = False
                        break
                    await save_output(socks_task.id, line)
                    output.append(line)
                    log.debug(line)

        result.files = []
        workdir_data = await container.get_archive("/workdir")
        log.debug("Retrieving files from workdir.")
        for entry in workdir_data.getmembers():
            if entry.isfile():
                filename = os.path.basename(entry.name)
                if filename in ignore_files:
                    continue
                log.debug(f"Uploading file {filename}")
                file_data = workdir_data.extractfile(entry)
                if file_data:
                    file_id = str(uuid.uuid4())
                    filename = os.path.basename(entry.name)
                    path = os.path.join("harbinger", f"{file_id}_{filename}")
                    async with FileUploader(
                        path, settings.minio_default_bucket
                    ) as uploader:
                        await uploader.upload(file_data.read())
                    result.files.append(
                        socks_schemas.File(
                            id=file_id,
                            filename=filename,
                            path=path,
                            bucket=settings.minio_default_bucket,
                        )
                    )
        try:
            await container.kill()
            await container.stop()
        except aiodocker.exceptions.DockerError:
            pass
        data = await container.show()
        result.exit_code = data["State"]["ExitCode"]
        await container.delete()
        result.status = schemas.Status.completed
        result.output = output
    except aiodocker.exceptions.DockerError as e:
        result.status = schemas.Status.error
        result.error = str(e)
        await save_output(socks_task.id, str(e))
    except Exception as e:
        result.status = schemas.Status.error
        result.error = str(e)
        await save_output(socks_task.id, str(e))
    finally:
        await docker.close()
    return result
