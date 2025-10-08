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

from datetime import timedelta

import structlog
from temporalio import workflow

from harbinger import schemas
from harbinger.config import constants
from harbinger.connectors.socks import activities
from harbinger.connectors.socks import schemas as socks_schemas

log = structlog.get_logger()


@workflow.defn(sandboxed=False)
class RunSocks:
    @workflow.run
    async def run(self, socks_task: schemas.ProxyJob) -> socks_schemas.SocksTaskResult:
        log.info(f"Running socks task: {socks_task.id}")
        status = schemas.ProxyJob(
            id=str(socks_task.id),
            status=schemas.Status.starting,
        )

        status.status = schemas.Status.running
        await workflow.execute_activity(
            activities.update_proxy_job_status,
            status,
            schedule_to_close_timeout=timedelta(hours=1),
            task_queue=constants.SOCKS_JOBS_QUEUE,
        )

        log.info(f"Running proxy job: {socks_task.id}")
        result = await workflow.execute_activity(
            activities.run_proxy_job,
            socks_schemas.SocksTask(
                command=socks_task.command,
                arguments=socks_task.arguments,
                id=str(socks_task.id),
                proxy=socks_task.proxy,
                tmate=socks_task.tmate,
                asciinema=socks_task.asciinema,
                proxychains=socks_task.proxychains,
                env=socks_task.env,
                files=socks_task.input_files,
                credential=socks_task.credential,
                docker_image=socks_task.docker_image,
            ),
            schedule_to_close_timeout=timedelta(days=365),
            task_queue=f"{constants.SOCKS_JOBS_QUEUE}_{socks_task.socks_server_id}",
        )
        if result.files:
            log.info("Saving files.")
            await workflow.execute_activity(
                activities.save_files,
                socks_schemas.Files(id=str(socks_task.id), files=result.files),
                task_queue=constants.SOCKS_JOBS_QUEUE,
                schedule_to_close_timeout=timedelta(hours=1),
            )
            for file in result.files:
                await workflow.start_child_workflow(
                    "ParseFile",
                    file.id,
                    task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
                    parent_close_policy=workflow.ParentClosePolicy.ABANDON,
                )

        status.status = result.status
        await workflow.execute_activity(
            activities.update_proxy_job_status,
            status,
            schedule_to_close_timeout=timedelta(hours=1),
            task_queue=constants.SOCKS_JOBS_QUEUE,
        )
        log.info(f"Finished socks task: {socks_task.id} with status: {result.status}")
        return result


# workflow:
# Create a docker volume [x]
# Create a container that downloads the required files from env variables [x]
# Run the command in the container [x]
# Stream the command results to redis / stuff [x]
# Create a container that uploads the new files to harbinger [x]
# For each file start a file workflow. [x]


@workflow.defn(sandboxed=False)
class RunWindowsSocks:
    @workflow.run
    async def run(self, socks_task: schemas.ProxyJob) -> socks_schemas.SocksTaskResult:
        log.info(f"Running socks task: {socks_task.id}")
        log.info("Updating status to running")
        await workflow.execute_activity(
            activities.update_proxy_job_status,
            schemas.ProxyJob(
                id=str(socks_task.id),
                status=schemas.Status.running,
            ),
            task_queue=constants.SOCKS_JOBS_QUEUE,
            schedule_to_close_timeout=timedelta(hours=1),
        )

        log.info("Running job on windows")

        r = await workflow.execute_activity(
            "ExecuteJobWindows",
            socks_task,
            task_queue=f"{constants.SOCKS_JOBS_QUEUE}_{socks_task.socks_server_id}",
            schedule_to_close_timeout=timedelta(hours=1),
        )

        result = socks_schemas.SocksTaskResult.model_validate(r)

        await workflow.execute_activity(
            activities.update_proxy_job_status,
            schemas.ProxyJob(
                id=str(socks_task.id),
                status=result.status,
                exit_code=result.exit_code,
            ),
            task_queue=constants.SOCKS_JOBS_QUEUE,
            schedule_to_close_timeout=timedelta(hours=1),
        )

        if result.files:
            log.info("Saving files.")
            from harbinger.worker.workflows import ParseFile

            await workflow.execute_activity(
                activities.save_files,
                socks_schemas.Files(id=str(socks_task.id), files=result.files),
                task_queue=constants.SOCKS_JOBS_QUEUE,
                schedule_to_close_timeout=timedelta(hours=1),
            )
            for file in result.files:
                await workflow.start_child_workflow(
                    ParseFile.run,
                    file.id,
                    task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
                    parent_close_policy=workflow.ParentClosePolicy.ABANDON,
                )

        log.info(f"Completed {socks_task.id} with status: {result.status}")
        return result

    @workflow.signal(name="output")
    async def handle_output(self, output: socks_schemas.Output) -> None:
        await workflow.execute_activity(
            activities.save_output_activity,
            output,
            task_queue=constants.SOCKS_JOBS_QUEUE,
            schedule_to_close_timeout=timedelta(hours=1),
        )
