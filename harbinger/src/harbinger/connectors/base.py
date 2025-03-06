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

from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker
import signal
from abc import abstractmethod, ABC
from datetime import datetime
import anyio
import structlog
import uuid
from harbinger.database import schemas
from anyio.abc import TaskGroup
from harbinger.database.redis_pool import redis
from harbinger.worker.client import get_client
from harbinger.connectors.config import get_settings
from pydantic import BaseModel
from asyncio import Queue, sleep
from harbinger.files.client import FileUploader
import grpc
from harbinger.proto.v1 import messages_pb2_grpc, messages_pb2
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message
from typing import Type


log = structlog.get_logger()

settings = get_settings()


class Connector(ABC):
    """
    Abstract base for Harbinger connectors.
    Make sure to implement the following methods:
    custom_create
    run_job
    start_tasks
    sync_all

    Set the name class variable.
    """

    name = "base"

    def __init__(
        self, c2_server_id: str, client: Client, stub: messages_pb2_grpc.HarbingerStub, channel: grpc.aio.Channel
    ) -> None:
        self.c2_server_id = c2_server_id
        self.client = client
        self.tg: TaskGroup | None = None
        self.disable_tasks = False
        self.running = False
        self.stub = stub
        self.channel = channel

        # Queues
        self.file_queue: Queue[schemas.FileCreate] = Queue()
        self.task_queue: Queue[schemas.C2TaskCreate] = Queue()
        self.output_queue: Queue[schemas.C2OutputCreate] = Queue()
        self.implant_queue: Queue[schemas.C2ImplantCreate] = Queue()
        self.proxy_queue: Queue[schemas.ProxyCreate] = Queue()
        self.task_status_queue: Queue[schemas.C2TaskStatus] = Queue()

    @classmethod
    async def create(cls, c2_server_id: str) -> "Connector":
        client = await get_client()
        channel = grpc.aio.insecure_channel(settings.harbinger_grpc_host)
        stub = messages_pb2_grpc.HarbingerStub(channel)
        await stub.Ping(messages_pb2.PingRequest(message="Test"))
        resp = await stub.GetSettings(messages_pb2.SettingsRequest(c2_server_id=c2_server_id))
        data = schemas.C2ServerAll(**MessageToDict(resp))
        return await cls.custom_create(c2_server_id, client, data, stub, channel)

    @classmethod
    @abstractmethod
    async def custom_create(
        cls,
        c2_server_id: str,
        client: Client,
        server_settings: schemas.C2ServerAll,
        stub: messages_pb2_grpc.HarbingerStub,
        channel: grpc.aio.Channel,
    ) -> "Connector":
        pass

    async def run(self):
        self.running = True
        try:
            async with anyio.create_task_group() as tg:
                self.tg = tg
                await self.create_tasks(tg)
                if self.disable_tasks:
                    log.warning("Not running tasks in this connector.")
                else:
                    tg.start_soon(self._worker_loop)

                tg.start_soon(self._data_loop)
                log.info("All task started, waiting for signal")
                with anyio.open_signal_receiver(
                    signal.SIGTERM, signal.SIGINT
                ) as signals:
                    async for signum in signals:
                        self.running = False
                        tg.cancel_scope.cancel()
                        break
        finally:
            await self.channel.close()
            await self.disconnect()
            await redis.aclose()

    async def send_c2_task_status(
        self,
        c2_task_status: schemas.C2TaskStatus,
    ) -> None:
        self.task_status_queue.put_nowait(c2_task_status)

    async def _worker_loop(self):
        queue = f"{self.c2_server_id}_jobs"
        # Run the worker
        worker = Worker(
            self.client,
            task_queue=queue,
            workflows=[],
            activities=[self._run_job, self._wait_for_task, self._sync_all],
        )
        await worker.run()

    @activity.defn(name="sync_all")
    async def _sync_all(self) -> None:
        log.info("Syncing all")
        await self.sync_all()
        log.info("Sync completed")

    @abstractmethod
    async def sync_all(self) -> None:
        raise NotImplementedError("Must be overwritten.")

    @activity.defn(name="run_job")
    async def _run_job(self, job: schemas.RunJob) -> schemas.C2TaskCreate:
        return await self.run_job(job.c2_job, job.c2_implant)

    @activity.defn(name="wait_for_task")
    async def _wait_for_task(
        self, c2_task: schemas.C2Task
    ) -> schemas.WorkflowStepResult:
        return await self.wait_for_task(c2_task)

    async def process_file(self, file: schemas.FileCreate) -> None:
        self.file_queue.put_nowait(file)

    async def save_task(self, task: schemas.C2TaskCreate) -> None:
        self.task_queue.put_nowait(task)

    async def save_output(
        self,
        output: schemas.C2OutputCreate,
    ) -> None:
        if output.response_text and len(output.response_text) > 1000:
            data = output.response_text.encode("utf-8", errors="replace")
            bucket: str = settings.minio_default_bucket
            path = f"{self.name}/output/{uuid.uuid4()}"
            async with FileUploader(path, bucket) as f:
                await f.upload(data)
            output.bucket = bucket
            output.path = path
            output.response_text = None
            output.response_bytes = None
        self.output_queue.put_nowait(output)

    async def save_implant(self, c2_implant: schemas.C2ImplantCreate) -> None:
        self.implant_queue.put_nowait(c2_implant)

    async def save_proxy(self, proxy: schemas.ProxyCreate) -> None:
        self.proxy_queue.put_nowait(proxy)

    @abstractmethod
    async def disconnect() -> None:
        pass

    @abstractmethod
    async def run_job(
        self, c2_job: schemas.C2Job, c2_implant: schemas.C2Implant
    ) -> schemas.C2TaskCreate:
        raise NotImplementedError("Must be overwritten.")

    @abstractmethod
    async def wait_for_task(
        self,
        c2_task: schemas.C2Task,
    ) -> schemas.WorkflowStepResult:
        raise NotImplementedError("Must be overwritten.")

    @abstractmethod
    async def create_tasks(self, tg: TaskGroup):
        """Do whatever initialization you need to do and start the tasks."""
        pass

    def pydantic_to_proto(self, pydantic_object: BaseModel, proto_object: Type[Message]) -> Message:
        result = proto_object()
        for key, value in pydantic_object.model_dump().items():
            if value:
                if isinstance(value, datetime):
                    value = str(value.timestamp())
                try:
                    setattr(result, key, value)
                except ValueError:
                    pass
        return result

    async def _data_loop(self):
        while self.running:
            while not self.file_queue.empty():
                file = await self.file_queue.get()
                req = self.pydantic_to_proto(file, messages_pb2.FileRequest)
                await self.stub.SaveFile(req)
                self.file_queue.task_done()

            while not self.task_queue.empty():
                task = await self.task_queue.get()
                req = self.pydantic_to_proto(task, messages_pb2.TaskRequest)
                await self.stub.SaveTask(req)
                self.task_queue.task_done()

            while not self.output_queue.empty():
                output = await self.output_queue.get()
                req = self.pydantic_to_proto(output, messages_pb2.TaskOutputRequest)
                await self.stub.SaveTaskOutput(req)
                self.output_queue.task_done()

            while not self.implant_queue.empty():
                implant = await self.implant_queue.get()
                req = self.pydantic_to_proto(implant, messages_pb2.ImplantRequest)
                await self.stub.SaveImplant(req)
                self.implant_queue.task_done()

            while not self.proxy_queue.empty():
                proxy = await self.proxy_queue.get()
                req = self.pydantic_to_proto(proxy, messages_pb2.ProxyRequest)
                await self.stub.SaveProxy(req)
                self.proxy_queue.task_done()

            while not self.task_status_queue.empty():
                task_status = await self.task_status_queue.get()
                req = self.pydantic_to_proto(task_status, messages_pb2.C2TaskStatusRequest)
                await self.stub.C2TaskStatus(req)
                self.task_status_queue.task_done()

            await sleep(0.5)
