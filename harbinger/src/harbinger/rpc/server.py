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
import uuid
from harbinger import schemas
from harbinger.worker import activities, workflows
from harbinger.worker.client import get_client
from harbinger.database.redis_pool import redis
import anyio
import structlog
import signal
from harbinger.config import constants
from harbinger.proto.v1 import messages_pb2_grpc, messages_pb2
from temporalio.client import Client
import grpc
from google.protobuf.json_format import MessageToDict
import logging
import click
from pydantic import ValidationError
from typing import AsyncIterable
from harbinger.files.client import FileUploader, download_file
from harbinger.config import get_settings

settings = get_settings()


log = structlog.get_logger()


@click.command()
@click.option("--debug", is_flag=True, show_default=True, default=False, help="Debug")
def cli(debug: bool):
    anyio.run(main, debug)


class Harbinger(messages_pb2_grpc.HarbingerServicer):

    def __init__(self, client: Client):
        self.running = True
        self.client = client
        self.implant_queue: asyncio.Queue[schemas.C2ImplantCreate] = asyncio.Queue()
        self.task_queue: asyncio.Queue[schemas.C2TaskCreate] = asyncio.Queue()
        self.task_output_queue: asyncio.Queue[schemas.C2OutputCreate] = asyncio.Queue()
        self.proxy_queue: asyncio.Queue[schemas.ProxyCreate] = asyncio.Queue()
        self.task_status_queue: asyncio.Queue[schemas.C2TaskStatus] = asyncio.Queue()
        self.file_queue: asyncio.Queue[schemas.FileCreate] = asyncio.Queue()

    async def worker_loop(self):
        while self.running:
            while not self.implant_queue.empty():
                c2_implant = self.implant_queue.get_nowait()
                log.debug(c2_implant)
                try:
                    await activities.save_implant(c2_implant)
                except Exception as e:
                    log.error(f"Error saving implant: {e}")
                    log.info(c2_implant)
                self.implant_queue.task_done()

            while not self.task_queue.empty():
                c2_task = self.task_queue.get_nowait()
                log.debug(c2_task)
                try:
                    await activities.save_task(c2_task)
                except Exception as e:
                    log.error(f"Error saving task: {e}")
                    log.info(c2_task)
                self.task_queue.task_done()

            while not self.task_output_queue.empty():
                c2_task_output = self.task_output_queue.get_nowait()
                # log.debug(c2_task_output)
                try:
                    output_created = await activities.save_task_output(c2_task_output)
                    if output_created.created:
                        log.debug(output_created.highest_process_number)
                        if output_created.highest_process_number:
                            await self.client.start_workflow(
                                workflows.LabelProcesses.run,
                                schemas.LabelProcess(
                                    host_id=str(output_created.host_id),
                                    number=output_created.highest_process_number,
                                ),
                                id=str(uuid.uuid4()),
                                task_queue=constants.WORKER_TASK_QUEUE,
                            )
                        else:
                            await self.client.start_workflow(
                                workflows.TextParser.run,
                                schemas.TextParse(
                                    text=output_created.output,
                                    c2_implant_id=output_created.c2_implant_id,
                                    c2_output_id=output_created.c2_output_id,
                                ),
                                id=str(uuid.uuid4()),
                                task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
                            )
                except Exception as e:
                    log.error(f"Error saving output: {e}")
                    # log.info(c2_task_output)
                self.task_output_queue.task_done()

            while not self.proxy_queue.empty():
                proxy = self.proxy_queue.get_nowait()
                log.debug(proxy)
                try:
                    await activities.save_proxy(proxy)
                except Exception as e:
                    log.error(f"Error saving task: {e}")
                    log.info(proxy)
                self.proxy_queue.task_done()

            while not self.task_status_queue.empty():
                c2_task_status = self.task_status_queue.get_nowait()
                log.debug(c2_task_status)
                try:
                    await activities.update_c2_task_status(c2_task_status)
                except Exception as e:
                    log.error(f"Error updating c2_task_status: {e}")
                    log.info(c2_task_status)
                self.task_status_queue.task_done()

            while not self.file_queue.empty():
                file = self.file_queue.get_nowait()
                log.info(f"New file: {file.filename}")
                try:
                    file_db = await activities.save_file(file)
                    if file_db:
                        await self.client.start_workflow(
                            workflows.ParseFile.run,
                            str(file_db.id),
                            id=str(uuid.uuid4()),
                            task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
                        )
                except Exception as e:
                    log.error(f"Error saving file: {e}")
                    log.info(file)
                self.file_queue.task_done()
            await asyncio.sleep(1)

    async def Ping(
        self, request: messages_pb2.PingRequest, context: grpc.aio.ServicerContext
    ) -> messages_pb2.PingResponse:
        return messages_pb2.PingResponse(message=f"Pong {request.message}")

    async def SaveImplant(
        self, request: messages_pb2.ImplantRequest, context: grpc.aio.ServicerContext
    ) -> messages_pb2.ImplantResponse:
        try:
            implant = schemas.C2ImplantCreate(
                **MessageToDict(request, preserving_proto_field_name=True)
            )
            self.implant_queue.put_nowait(implant)
        except ValidationError as e:
            log.warning(f"Validation error while parsing: {request}: {e}")
        return messages_pb2.ImplantResponse()

    async def SaveProxy(
        self, request: messages_pb2.ProxyRequest, context: grpc.aio.ServicerContext
    ) -> messages_pb2.ProxyResponse:
        try:
            proxy = schemas.ProxyCreate(
                **MessageToDict(request, preserving_proto_field_name=True)
            )
            self.proxy_queue.put_nowait(proxy)
        except ValidationError:
            log.warning(f"Validation error while parsing: {request}")

        return messages_pb2.ProxyResponse()

    async def SaveFile(
        self, request: messages_pb2.FileRequest, context: grpc.aio.ServicerContext
    ) -> messages_pb2.FileResponse:
        try:
            bucket = request.bucket
            path = request.path
            if request.upload_file_id:
                bucket = settings.minio_default_bucket
                path = f"upload/{request.upload_file_id}"

            file = schemas.FileCreate(
                filename=request.filename,
                bucket=bucket,
                path=path,
                c2_server_id=request.c2_server_id,
                internal_task_id=request.internal_task_id,
                internal_implant_id=request.internal_implant_id,
            )
            self.file_queue.put_nowait(file)
        except ValidationError:
            log.warning(f"Validation error while parsing: {request}")

        return messages_pb2.FileResponse()

    async def C2TaskStatus(
        self,
        request: messages_pb2.C2TaskStatusRequest,
        context: grpc.aio.ServicerContext,
    ) -> messages_pb2.C2TaskStatusResponse:
        try:
            task_status = schemas.C2TaskStatus(
                **MessageToDict(request, preserving_proto_field_name=True)
            )
            self.task_status_queue.put_nowait(task_status)
        except ValidationError:
            log.warning(f"Validation error while parsing: {request}")

        return messages_pb2.C2TaskStatusResponse()

    async def GetSettings(
        self, request: messages_pb2.SettingsRequest, context: grpc.aio.ServicerContext
    ) -> messages_pb2.SettingsResponse:
        try:
            data = await activities.get_server_settings(request.c2_server_id)
            if data:
                return messages_pb2.SettingsResponse(**data.model_dump())
        except ValidationError:
            log.warning(f"Validation error while parsing: {request}")

        return messages_pb2.SettingsResponse()

    async def SaveTask(
        self, request: messages_pb2.TaskRequest, context: grpc.aio.ServicerContext
    ) -> messages_pb2.TaskResponse:
        try:
            task = schemas.C2TaskCreate(
                **MessageToDict(request, preserving_proto_field_name=True)
            )
            self.task_queue.put_nowait(task)
        except ValidationError:
            log.warning(f"Validation error while parsing: {request}")

        return messages_pb2.TaskResponse()

    async def SaveTaskOutput(
        self, request: messages_pb2.TaskOutputRequest, context: grpc.aio.ServicerContext
    ) -> messages_pb2.TaskOutputResponse:
        try:
            task_output = schemas.C2OutputCreate(
                **MessageToDict(request, preserving_proto_field_name=True)
            )
            self.task_output_queue.put_nowait(task_output)
        except ValidationError as e:
            log.warning(f"Validation error while parsing: {e}")
        return messages_pb2.TaskOutputResponse()

    async def CheckFileExists(
        self, request: messages_pb2.FileExistsRequest, context: grpc.aio.ServicerContext
    ) -> messages_pb2.FileExistsResponse:
        found = False
        if request.sha1:
            found = await activities.check_file_hash(request.sha1)
        if request.sha256:
            found = await activities.check_file_hash(request.sha256)
        if request.md5:
            found = await activities.check_file_hash(request.md5)
        return messages_pb2.FileExistsResponse(exists=found)

    async def UploadFile(
        self,
        request_iterator: AsyncIterable[messages_pb2.UploadFileRequest],
        context: grpc.ServicerContext,
    ) -> messages_pb2.UploadFileResponse:
        file_id = str(uuid.uuid4())
        bucket = settings.minio_default_bucket
        path = f"upload/{file_id}"
        async with FileUploader(path, bucket) as f:
            async for entry in request_iterator:
                await f.upload(entry.data)
        return messages_pb2.UploadFileResponse(upload_file_id=file_id)

    async def DownloadFile(
        self,
        request: messages_pb2.DownloadFileRequest,
        context: grpc.aio.ServicerContext,
    ) -> AsyncIterable[messages_pb2.DownloadFileResponse]:
        if not request.file_id:
            raise RuntimeError("No file_id provided")

        file_db = await activities.get_file(request.file_id)
        if not file_db:
            raise RuntimeError("File not found")

        data = await download_file(file_db.path, file_db.bucket)
        for i in range(0, len(data), 1024 * 1024):
            yield messages_pb2.DownloadFileResponse(data=data[i : i + 1024 * 1024])

    async def SetC2ServerStatus(
        self,
        request: messages_pb2.C2ServerStatusRequest,
        context: grpc.aio.ServicerContext,
    ) -> messages_pb2.C2ServerStatusResponse:
        try:
            await activities.update_c2_server_status(
                schemas.C2ServerStatusUpdate(
                    c2_server_id=request.c2_server_id,
                    status=schemas.C2ServerStatus(
                        status=request.status,
                        name=request.name,
                    ),
                )
            )
        except ValidationError:
            log.warning(f"Validation error while parsing: {request}")
        return messages_pb2.C2ServerStatusResponse()

async def main(debug: bool = False):
    log.info(f"Starting grpc server, debug: {debug}")
    client = await get_client()

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if debug else logging.INFO
        ),
    )

    server = grpc.aio.server()
    harbinger = Harbinger(client)
    messages_pb2_grpc.add_HarbingerServicer_to_server(harbinger, server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    log.info(f"Starting server on {listen_addr}")
    await server.start()
    try:
        async with anyio.create_task_group() as tg:
            tg.start_soon(harbinger.worker_loop)
            tg.start_soon(server.wait_for_termination)
            log.info("Server started, waiting for signal.")
            with anyio.open_signal_receiver(signal.SIGTERM, signal.SIGINT) as signals:
                async for signum in signals:
                    log.info(f"Received {signum} stopping grpc server")
                    harbinger.running = False
                    tg.cancel_scope.cancel()
                    await server.stop(5.0)
                    log.info("Shutdown done!")
                    break
        log.info("Done")
    finally:
        await redis.aclose()


if __name__ == "__main__":
    cli()
