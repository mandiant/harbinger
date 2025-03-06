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
import click
from harbinger.database.database import SessionLocal
from harbinger.database import crud, schemas
import structlog
from harbinger.config import get_settings
import asyncio
import signal
import uuid
from harbinger.worker.client import get_client
from temporalio.worker import Worker
from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
    ScheduleAlreadyRunningError,
)
from temporalio.service import RPCError
from harbinger.connectors import workflows
from harbinger.connectors import activities
from harbinger.connectors.socks import workflows as socks_workflows
from harbinger.connectors.socks import activities as socks_activities
from harbinger.database.redis_pool import redis

settings = get_settings()

log = structlog.get_logger()


@click.command()
def cli():
    anyio.run(main)


SOCKS_QUEUE = "socks_jobs"
DEFAULT_HARBINGER_SOCKS_SERVER = uuid.UUID("dfe9668d-fda8-4f96-a4b4-b4db843a7b02")


async def create_socks_server():
    async with SessionLocal() as db:
        await crud.create_socks_server(
            db,
            schemas.SocksServerCreate(
                id=DEFAULT_HARBINGER_SOCKS_SERVER,
                hostname="harbinger",
                operating_system=schemas.ExecutorTypeName.linux,
                type=schemas.SocksServerType.docker,
                status=schemas.Status.running,
            ),
        )
        await db.commit()


async def update_status(status: str) -> None:
    async with SessionLocal() as db:
        await crud.update_socks_server_status(
            db,
            id=DEFAULT_HARBINGER_SOCKS_SERVER,
            status=status,
        )


async def main():
    log.info("Starting docker worker")
    client = await get_client()
    worker = Worker(
        client,
        task_queue="c2_server_commands",
        workflows=[workflows.C2ServerCommand, workflows.C2ServerLoop],
        activities=[
            activities.start,
            activities.stop,
            activities.restart,
            activities.create,
            activities.delete,
            activities.loop,
        ],
    )
    worker2 = Worker(
        client,
        task_queue=f"socks_jobs_{str(DEFAULT_HARBINGER_SOCKS_SERVER)}",
        workflows=[],
        activities=[
            socks_activities.run_proxy_job,
        ],
    )
    worker3 = Worker(
        client,
        task_queue=SOCKS_QUEUE,
        workflows=[
            socks_workflows.RunSocks,
            socks_workflows.RunWindowsSocks,
        ],
        activities=[
            socks_activities.update_proxy_job_status,
            socks_activities.save_files,
            socks_activities.save_output_activity,
        ],
    )
    asyncio.create_task(worker.run())
    asyncio.create_task(worker2.run())
    asyncio.create_task(worker3.run())

    await create_socks_server()

    # delete older cron version of the loop
    handle = client.get_workflow_handle(workflow_id="workflow-loop")
    if handle:
        try:
            await handle.terminate()
        except RPCError:
            pass

    # create new schedule based.
    try:
        await client.create_schedule(
            "check-container-states",
            Schedule(
                action=ScheduleActionStartWorkflow(
                    workflows.C2ServerLoop.run,
                    id="check-container-states",
                    task_queue="c2_server_commands",
                ),
                spec=ScheduleSpec(
                    cron_expressions=["* * * * *"],
                ),
            ),
        )
    except ScheduleAlreadyRunningError:
        pass

    try:
        with anyio.open_signal_receiver(signal.SIGTERM, signal.SIGINT) as signals:
            log.info("Worker started, waiting for signal.")
            async for signum in signals:
                log.info(f"Received {signum} stopping workers")
                await worker.shutdown()
                await worker2.shutdown()
                await worker3.shutdown()
                break
        log.info("Done")
    finally:
        await redis.aclose()
        await update_status(schemas.Status.disconnected)


@click.command()
def connector():
    anyio.run(main_connector)


async def main_connector() -> None:
    log.info("Starting worker")


if __name__ == "__main__":
    cli()
