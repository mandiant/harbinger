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

import os
from temporalio import activity
from harbinger.config import get_settings
from harbinger.database import crud
from harbinger import schemas
from harbinger.database.database import SessionLocal
import structlog
import aiodocker
from harbinger.connectors.socks.environment import get_environment, SERVER_ENV

settings = get_settings()
log = structlog.get_logger()


@activity.defn
async def create(
    server_command: schemas.C2ServerCommand
):
    log.info(f"Running create command for {server_command.id}")
    if not server_command.c2_server:
        log.warning("Unable to find the c2_server")
        return
        return
    c2_server = server_command.c2_server
    if not c2_server.type:
        log.warning("Unable to find the c2_server")
        return
    environment = await get_environment(SERVER_ENV)
    async with SessionLocal() as session:
        c2_server_type = await crud.get_c2_server_type_by_name(session, c2_server.type)
        if not c2_server_type:
            log.warning(f"Unable to find type {c2_server.type}")
            return

        name = f"{c2_server.type}_{str(c2_server.id)[0:8]}"
        connectors = []
        await create_new_c2(
            c2_server_id=str(c2_server.id),
            environment=environment,
            name=name,
            connector_type=c2_server.type,
            image=c2_server_type.docker_image,
            command=c2_server_type.command,
        )
        connectors.append(c2_server.type)

    async with SessionLocal() as session:
        for name in connectors:
            await crud.update_c2_server_status(
                session,
                c2_server.id,
                schemas.C2ServerStatus(status=schemas.Status.created, name=name),
            )

@activity.defn
async def start(
    server_command: schemas.C2ServerCommand,
):
    docker = aiodocker.Docker()
    try:
        log.info(f"Running start command for {server_command.id}")
        if not server_command.c2_server:
            log.info("C2 server was not set, returning")
            return
        async with SessionLocal() as session:
            for container in await docker.containers.list(
                all=True,
                filters=dict(label=[f"type={server_command.name}", f"c2_server_id={server_command.id}"]),
            ):
                await container.start()
                await crud.update_c2_server_status(
                    session,
                    server_command.c2_server.id,
                    schemas.C2ServerStatus(
                        status=schemas.Status.starting, name=server_command.name
                    ),
                )
                log.info(f"Completed start command for {server_command.id}")
                return
        log.warning(
            f"Was not able to find a correct container for: id: <{server_command.id}> name: <{server_command.name}>"
        )
    except aiodocker.exceptions.DockerError as e:
        log.warning(f"Unable to access the docker socket: {e}")
    finally:
        await docker.close()

@activity.defn
async def stop(
    server_command: schemas.C2ServerCommand,
):
    docker = aiodocker.Docker() 
    try:
        log.info(f"Running stop command for {server_command.id}")
        if not server_command.name:
            log.info("Name was not set, returning")
            return
        if not server_command.c2_server:
            log.info("C2 server was not set, returning")
            return
        async with SessionLocal() as session:
            for container in await docker.containers.list(
                all=True,
                filters=dict(label=[f"type={server_command.name}", f"c2_server_id={server_command.id}"]),
            ):
                await container.stop()
                await crud.update_c2_server_status(
                    session,
                    server_command.c2_server.id,
                    schemas.C2ServerStatus(
                        status=schemas.Status.stopping, name=server_command.name
                    ),
                )
                log.info(f"Completed stop command for {server_command.id}")
                return
            log.warning(
                f"Was not able to find a correct container for: id: <{server_command.id}> name: <{server_command.name}>"
        )
    except aiodocker.exceptions.DockerError as e:
        log.warning(f"Unable to access the docker socket: {e}")
    finally:
        await docker.close()

@activity.defn
async def restart(
    server_command: schemas.C2ServerCommand,
):
    docker = aiodocker.Docker()
    try:
        log.info(f"Running restart command for {server_command.id}")
        if not server_command.name or not server_command.id:
            log.info("Required fields were not set, returning")
            return

        async with SessionLocal() as session:
            for container in await docker.containers.list(
                all=True,
                filters=dict(label=[f"type={server_command.name}", f"c2_server_id={server_command.id}"]),
            ):
                await container.restart()
                await crud.update_c2_server_status(
                    session,
                    server_command.id,
                    schemas.C2ServerStatus(
                        status=schemas.Status.restarted, name=server_command.name
                    ),
                )
                log.info(f"Completed restart command for {server_command.id}")
                return
        log.warning(
            f"Was not able to find a correct container for: id: <{server_command.id}> name: <{server_command.name}>"
        )
    except aiodocker.exceptions.DockerError as e:
        log.warning(f"Unable to access the docker socket: {e}")
    finally:
        await docker.close()


@activity.defn
async def delete(
    server_command: schemas.C2ServerCommand,
):
    log.info(f"Running delete command for {server_command.id}")
    docker = aiodocker.Docker()
    try:
        if not server_command.name or not server_command.id:
            log.info("Required fields were not set, returning")
            return
        async with SessionLocal() as session:
            for container in await docker.containers.list(
                all=True,
                filters=dict(label=[f"type={server_command.name}", f"c2_server_id={server_command.id}"]),
            ):
                await container.stop()
                await container.delete()
                await crud.delete_c2_server_status_custom(
                    session,
                    server_command.id,
                    schemas.C2ServerStatus(
                        status=schemas.Status.deleting, name=server_command.name
                    ),
                )
                return
        log.warning(
            f"Was not able to find a correct container for: id: <{server_command.id}> name: <{server_command.name}>"
        )
    except aiodocker.exceptions.DockerError as e:
        log.warning(f"Unable to access the docker socket: {e}")
    finally:
        await docker.close()

async def create_new_c2(
    c2_server_id: str,
    environment: list[str],
    name: str,
    image: str,
    command: str,
    connector_type: str,
):
    docker = aiodocker.Docker()
    network = await docker.networks.get('harbinger')
    attrs = await network.show()
    dns_ip = attrs.get("IPAM", {}).get("Config", [{}])[0].get("Gateway", '')
    try:
        environment.append(f"C2_SERVER_ID={c2_server_id}")
        config = {
            "Image": image,
            "AttachStdin": False,
            "AttachStdout": False,
            "AttachStderr": False,
            "Tty": False,
            "OpenStdin": False,
            "Labels": dict(c2_server_id=c2_server_id, type=connector_type),
            "Name": f"harbinger_{name}",
            "HostConfig": {
                "NetworkMode": "harbinger",
                "Dns": [dns_ip] if dns_ip else [],
            },
            "NetworkMode": "harbinger",
            "Env": environment,
            "RestartPolicy": dict(Name="unless-stopped"),
        }
        if command:
            config["Cmd"] = command

        container = await docker.containers.create(
            config=config,
            name=f"harbinger_{name}",
        )
        await container.start()
        log.info(f"Created container: {container.id}")
    finally:
        await docker.close()


@activity.defn
async def loop():
    data = {}
    docker = aiodocker.Docker()
    try:
        for container in await docker.containers.list(all=True):
            res = await container.show()
            labels = res["Config"]["Labels"]
            state = res["State"]["Status"]
            if "c2_server_id" in labels and "type" in labels:
                c2_server_id = labels["c2_server_id"]
                c2_type = labels["type"]
                if c2_server_id not in data:
                    data[c2_server_id] = {}
                data[c2_server_id][c2_type] = state
        async with SessionLocal() as db:
            status_list = await crud.list_c2_server_status(db)
            for status in status_list:
                if str(status.c2_server_id) in data:
                    if status.name in data[str(status.c2_server_id)]:
                        state = data[str(status.c2_server_id)][status.name]
                        log.debug(
                            f"Updating status to: {state} of {status.name} of {status.c2_server_id}"
                        )
                        await crud.update_c2_server_status(
                            db,
                            status.c2_server_id,
                            schemas.C2ServerStatus(status=state, name=status.name),
                        )
                        await db.commit()
                    else:
                        log.info(
                            f"Cannot find the container relating to {status.id} deleting entry."
                        )
                        await crud.delete_c2_server_status(db, status.id)
                else:
                    log.info(
                        f"Cannot find the container relating to {status.id} deleting entry."
                    )
                    await crud.delete_c2_server_status(db, status.id)
    except aiodocker.exceptions.DockerError as e:
        log.warning(f"Unable to access the docker socket: {e}")
    finally:
        await docker.close()
