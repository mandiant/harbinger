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

from harbinger.config import constants
from temporalio import workflow, common
from datetime import timedelta
from graphlib import TopologicalSorter, CycleError
import asyncio
import structlog
import re

from harbinger.worker import activities
from harbinger.database import schemas, progress_bar
from harbinger.connectors.socks.workflows import RunSocks, RunWindowsSocks
from harbinger.connectors.socks import activities as socks_activities
from harbinger.connectors.socks import schemas as socks_schemas

log = structlog.get_logger()


class ProgressBarMixin:

    def __init__(self):
        self.bar = schemas.ProgressBar()

    async def delete_bar(self) -> None:
        await workflow.execute_activity(
            activities.delete_progress_bar,
            self.bar,
            task_queue=constants.WORKER_TASK_QUEUE,
            schedule_to_close_timeout=timedelta(seconds=120),
        )

    async def increase(self, step: int = 1) -> None:
        self.bar.increase(step)
        await workflow.execute_activity(
            activities.update_progress_bar,
            self.bar,
            task_queue=constants.WORKER_TASK_QUEUE,
            schedule_to_close_timeout=timedelta(seconds=120),
        )

    async def create_bar(self, bar: schemas.ProgressBar) -> None:
        self.bar = bar
        await workflow.execute_activity(
            activities.create_progress_bar,
            self.bar,
            task_queue=constants.WORKER_TASK_QUEUE,
            schedule_to_close_timeout=timedelta(seconds=120),
        )


@workflow.defn(sandboxed=False)
class RunPlaybook(ProgressBarMixin):

    async def update_step(
        self,
        step: schemas.ChainStep,
        data: str,
        output_path: str,
    ) -> None:
        log.info(f"Updating step with {data} to {output_path}")
        if step.c2_job_id:
            await workflow.execute_activity(
                activities.update_c2_job,
                schemas.PlaybookStepModifierEntry(
                    input_path="",
                    output_path=output_path,
                    data=data,
                    c2_job_id=step.c2_job_id,
                    playbook_step_id=step.id,
                ),
                schedule_to_close_timeout=timedelta(seconds=20),
            )
        elif step.proxy_job_id:
            await workflow.execute_activity(
                activities.update_proxy_job,
                schemas.PlaybookStepModifierEntry(
                    input_path="",
                    output_path=output_path,
                    data=data,
                    proxy_job_id=step.proxy_job_id,
                    playbook_step_id=step.id,
                ),
                schedule_to_close_timeout=timedelta(seconds=20),
            )

    async def run_c2_step(
        self,
        step: schemas.ChainStep,
        result_queue: asyncio.Queue[schemas.WorkflowStepResult],
    ) -> None:

        c2_job = await workflow.execute_activity(
            activities.get_c2_job,
            str(step.c2_job_id),
            schedule_to_close_timeout=timedelta(seconds=5),
        )
        if not c2_job:
            raise ValueError(f"Job for job id: {step.c2_job_id} was not found.")

        implant = await workflow.execute_activity(
            activities.get_c2_implant,
            str(c2_job.c2_implant_id),
            schedule_to_close_timeout=timedelta(seconds=5),
        )
        if not implant:
            # TODO create harbinger exceptions
            raise ValueError(f"Implant for job id: {step.c2_job_id} was not found.")

        if step.delay:
            await workflow.execute_activity(
                activities.update_playbook_step_status,
                schemas.ChainStep(
                    id=step.id,
                    playbook_id=step.playbook_id,
                    status=schemas.Status.scheduled,
                ),
                schedule_to_close_timeout=timedelta(seconds=120),
            )
            log.info(f"Waiting for {step.delay.total_seconds()} for step {step.id}")
            await asyncio.sleep(step.delay.total_seconds())

        await workflow.execute_activity(
            activities.update_playbook_step_status,
            schemas.ChainStep(
                id=step.id,
                playbook_id=step.playbook_id,
                status=schemas.Status.starting,
            ),
            schedule_to_close_timeout=timedelta(seconds=120),
        )

        queue = f"{implant.c2_server_id}_jobs"
        result = await workflow.execute_activity(
            "run_job",
            schemas.RunJob(c2_job=c2_job, c2_implant=implant),
            task_queue=queue,
            schedule_to_close_timeout=timedelta(seconds=60 * 60 * 24 * 365),
        )
        c2_task_create = schemas.C2TaskCreate(**result)

        resp = await workflow.execute_activity(
            activities.save_task,
            c2_task_create,
            schedule_to_close_timeout=timedelta(seconds=120),
        )

        await workflow.execute_activity(
            activities.update_c2_job_c2_task_id,
            schemas.C2JobTaskMapping(
                c2_job_id=c2_job.id,
                c2_task_id=resp.id,
            ),
            schedule_to_close_timeout=timedelta(seconds=120),
        )

        workflow_result_raw = await workflow.execute_activity(
            "wait_for_task",
            resp,
            task_queue=queue,
            schedule_to_close_timeout=timedelta(seconds=60 * 60 * 24 * 365),
        )

        workflow_result = schemas.WorkflowStepResult(**workflow_result_raw)
        workflow_result.label = str(step.label)
        await workflow.execute_activity(
            activities.update_playbook_step_status,
            schemas.ChainStep(
                id=step.id,
                playbook_id=step.playbook_id,
                status=workflow_result.status,
            ),
            schedule_to_close_timeout=timedelta(seconds=120),
        )
        result_queue.put_nowait(workflow_result)

    async def run_proxy_step(
        self,
        step: schemas.ChainStep,
        result_queue: asyncio.Queue[schemas.WorkflowStepResult],
    ) -> None:
        job = await workflow.execute_activity(
            activities.get_proxy_job,
            str(step.proxy_job_id),
            schedule_to_close_timeout=timedelta(seconds=5),
        )
        if not job:
            raise ValueError(f"Implant for job id: {step.c2_job_id} was not found.")

        if step.delay:
            await workflow.execute_activity(
                activities.update_playbook_step_status,
                schemas.ChainStep(
                    id=step.id,
                    playbook_id=step.playbook_id,
                    status=schemas.Status.scheduled,
                ),
                schedule_to_close_timeout=timedelta(seconds=120),
            )
            log.info(f"Waiting for {step.delay.total_seconds()} for step {step.id}")
            await asyncio.sleep(step.delay.total_seconds())

        await workflow.execute_activity(
            activities.update_playbook_step_status,
            schemas.ChainStep(
                id=step.id,
                playbook_id=step.playbook_id,
                status=schemas.Status.starting,
            ),
            schedule_to_close_timeout=timedelta(seconds=120),
        )

        workflow_name = RunSocks.run
        if job.socks_server and job.socks_server.operating_system == "windows":
            workflow_name = RunWindowsSocks.run

        result = await workflow.execute_child_workflow(
            workflow_name,
            job,
            task_queue=f"socks_jobs",
            retry_policy=common.RetryPolicy(maximum_attempts=1),
        )

        result_queue.put_nowait(
            schemas.WorkflowStepResult(
                id=result.id,
                status=result.status,
                output="\n".join(result.output) if result.output else "",
                label=step.label,  # type: ignore
            )
        )

    async def run_empty_step(
        self,
        step: schemas.ChainStep,
        result_queue: asyncio.Queue[schemas.WorkflowStepResult],
    ) -> None:
        log.warning("Running empty step.")
        if step.delay:
            await workflow.execute_activity(
                activities.update_playbook_step_status,
                schemas.ChainStep(
                    id=step.id,
                    playbook_id=step.playbook_id,
                    status=schemas.Status.scheduled,
                ),
                schedule_to_close_timeout=timedelta(seconds=120),
            )
            log.info(f"Waiting for {step.delay.total_seconds()} for step {step.id}")
            await asyncio.sleep(step.delay.total_seconds())

        result_queue.put_nowait(
            schemas.WorkflowStepResult(
                id=step.id,
                label=str(step.label),
                status=schemas.Status.completed,
            )
        )

    @workflow.run
    async def run(self, playbook_id: str) -> None:
        await workflow.execute_activity(
            activities.update_playbook_status,
            schemas.ProxyChain(id=playbook_id, status=schemas.Status.running, steps=0),
            schedule_to_close_timeout=timedelta(seconds=120),
        )
        steps: list[schemas.ChainStep] = await workflow.execute_activity(
            activities.get_playbook_steps,
            playbook_id,
            schedule_to_close_timeout=timedelta(seconds=5),
        )

        bar = schemas.ProgressBar(
            type="playbook",
            id=playbook_id,
            description=f"Running playbook",
            max=len(steps),
        )
        await self.create_bar(bar)

        ts: TopologicalSorter = TopologicalSorter()

        log.info(f"[{playbook_id}] Running playbook with {len(steps)} steps!")

        steps_dict = {str(step.label): step for step in steps}

        for step in steps:
            depends_on = []
            if step.depends_on:
                depends_on = step.depends_on.split(",")
            ts.add(step.label, *depends_on)

        try:
            ts.prepare()
        except CycleError:
            log.info(f"[{playbook_id}] has a cycle in the dependencies.")
            await workflow.execute_activity(
                activities.update_playbook_status,
                schemas.ProxyChain(
                    id=playbook_id, status=schemas.Status.error, steps=0
                ),
                schedule_to_close_timeout=timedelta(seconds=120),
            )

        result_queue: asyncio.Queue[schemas.WorkflowStepResult] = asyncio.Queue()
        count = 0
        results_dict: dict[str, dict] = {}
        try:
            while ts.is_active():
                for node_label in ts.get_ready():
                    log.info(f"[{playbook_id}] Node label: {node_label}")
                    try:
                        node = steps_dict[node_label]
                        if node.step_modifiers:
                            for s in node.step_modifiers:
                                log.info("Modifying job based on previous results.")
                                try:
                                    data = results_dict[s.input_path]
                                    output = ""
                                    for i in range(3):
                                        output = await workflow.start_activity(
                                            activities.get_c2_task_output,
                                            data['id'],
                                            schedule_to_close_timeout=timedelta(seconds=120),
                                        )
                                        if not output:
                                            log.info(f"Did not receive output, waiting for {i*2 + 1} seconds")
                                            await asyncio.sleep(i*2 + 1)
                                    if s.regex:
                                        t = re.compile(s.regex)
                                        match = t.search(output)
                                        if match:
                                            output = match.group(0)
                                        else:
                                            log.warning(
                                                "Unable to match the regex..."
                                            )
                                            continue
                                    await self.update_step(
                                        node,
                                        output,
                                        s.output_path,
                                    )
                                except KeyError:
                                    log.warning(
                                        f"Could not find {s.input_path} in results_dict"
                                    )
                                    continue
                                except ValueError:
                                    log.warning(f"ValueError on {s.input_path}")
                                    continue
                        if node.c2_job_id:
                            asyncio.create_task(self.run_c2_step(node, result_queue))
                        elif node.proxy_job_id:
                            asyncio.create_task(self.run_proxy_step(node, result_queue))
                        else:
                            asyncio.create_task(self.run_empty_step(node, result_queue))
                    except KeyError:
                        result_queue.put_nowait(
                            schemas.WorkflowStepResult(
                                id="", label=node_label, status=schemas.Status.error
                            )
                        )
                finished_node = await result_queue.get()
                ts.done(finished_node.label)
                await self.increase(1)
                results_dict[finished_node.label] = finished_node.model_dump()
                count += 1
                await workflow.start_activity(
                    activities.update_playbook_status,
                    schemas.ProxyChain(
                        id=playbook_id, status=schemas.Status.running, steps=count
                    ),
                    schedule_to_close_timeout=timedelta(seconds=120),
                )
                result_queue.task_done()
                if finished_node.id:
                    step = schemas.ChainStep(
                        id=finished_node.id,  # type: ignore
                        status=finished_node.status,
                        playbook_id=playbook_id,
                    )
                    await workflow.start_activity(
                        activities.update_playbook_step_status,
                        step,
                        schedule_to_close_timeout=timedelta(seconds=120),
                    )
        except ValueError:
            await workflow.execute_activity(
                activities.update_playbook_status,
                schemas.ProxyChain(
                    id=playbook_id, status=schemas.Status.error, steps=len(steps)
                ),
                schedule_to_close_timeout=timedelta(seconds=120),
            )
        else:
            await workflow.execute_activity(
                activities.update_playbook_status,
                schemas.ProxyChain(
                    id=playbook_id, status=schemas.Status.completed, steps=len(steps)
                ),
                schedule_to_close_timeout=timedelta(seconds=120),
            )
        await self.delete_bar()
        log.info(f"[{playbook_id}] completed!")

    @workflow.signal(name="output")
    async def handle_output(self, output: socks_schemas.Output) -> None:
        await workflow.execute_activity(
            socks_activities.save_output_activity,
            output,
            task_queue=constants.SOCKS_JOBS_QUEUE,
            schedule_to_close_timeout=timedelta(hours=1),
        )


@workflow.defn(sandboxed=False)
class RunC2Job:

    @workflow.run
    async def run(self, job: schemas.C2Job) -> None:
        implant = await workflow.execute_activity(
            activities.get_c2_implant,
            str(job.c2_implant_id),
            schedule_to_close_timeout=timedelta(seconds=5),
        )
        if not implant:
            # TODO create harbinger exceptions
            raise ValueError(f"Implant for job id: {job.id} was not found.")

        c2_job = await workflow.execute_activity(
            activities.get_c2_job,
            str(job.id),
            schedule_to_close_timeout=timedelta(seconds=5),
        )
        if not c2_job:
            raise ValueError(f"Job for job id: {job.id} was not found.")

        queue = f"{implant.c2_server_id}_jobs"

        response = await workflow.execute_activity(
            "run_job",
            schemas.RunJob(c2_job=c2_job, c2_implant=implant),
            task_queue=queue,
            schedule_to_close_timeout=timedelta(seconds=60 * 60 * 24 * 365),
        )
        status = response.get("status", "")
        if status:
            job.status = status
            await workflow.execute_activity(
                activities.update_c2_job_status,
                job,
                schedule_to_close_timeout=timedelta(seconds=5),
            )


# All the files that do not need multiple steps or are the final step.
BASIC_PARSING_MAP: dict[schemas.FileType | str, str] = {
    schemas.FileType.pypykatz_json: "process_pypykatz",
    schemas.FileType.process_list_json: "process_proces_list",
    schemas.FileType.dir2json: "process_dir2json",
    schemas.FileType.kdbx: "process_kdbx",
    schemas.FileType.cast: "process_cast",
    schemas.FileType.certipy_json: "process_certipy_json",
    schemas.FileType.certify_json: "process_certify_json",
}

# All the files that will potentially yield a new filetype.
BASE_FILETYPE_PARSING_MAP: dict[schemas.FileType | str, str] = {
    schemas.FileType.text: "process_text",
    schemas.FileType.zip: "process_zip",
    schemas.FileType.json: "process_json",
    schemas.FileType.empty: "process_unknown",
}

# All the files that will yield new files.
FILE_YIELDING_PARSING_MAP: dict[schemas.FileType | str, str] = {
    schemas.FileType.nanodump: "process_nanodump",
    schemas.FileType.lsass: "process_lsass",
    schemas.FileType.ad_snapshot: "process_ad_snapshot",
    schemas.FileType.harbinger_zip: "process_harbinger_zip",
    schemas.FileType.ccache: "process_ccache",
    schemas.FileType.harbinger_yaml: "process_harbinger_yaml",
}


@workflow.defn(sandboxed=False, name="ParseFile")
class ParseFile(ProgressBarMixin):

    @workflow.run
    async def run(self, file_id: str) -> None:
        log.info(f"Parsing file: {file_id}")
        bar = schemas.ProgressBar(
            type="file", id=file_id, description=f"Processing file"
        )
        await self.create_bar(bar)
        try:
            file = await workflow.execute_activity(
                activities.get_file,
                file_id,
                schedule_to_close_timeout=timedelta(seconds=600),
            )
            await self.increase(10)
            if not file:
                log.warning("File was not found, returning")
                return

            file2 = await workflow.execute_activity(
                activities.FileParsing().file_magic_all,
                file,
                schedule_to_close_timeout=timedelta(seconds=1200),
            )
            if not file2:
                log.warning("File was not found, returning")
                return
            await self.increase(10)

            if file2.filetype is None:
                file2.filetype = schemas.FileType.empty

            if file2.filetype in BASIC_PARSING_MAP:
                await workflow.execute_activity(
                    BASIC_PARSING_MAP[file2.filetype],
                    file,
                    schedule_to_close_timeout=timedelta(seconds=1200),
                )
                await self.increase(80)
            elif file2.filetype in FILE_YIELDING_PARSING_MAP:
                new_files: list[dict] = await workflow.execute_activity(
                    FILE_YIELDING_PARSING_MAP[file2.filetype],
                    file,
                    schedule_to_close_timeout=timedelta(seconds=1200),
                )
                if new_files:
                    increase = int(80 / len(new_files))
                    for new_file in new_files:
                        await workflow.execute_child_workflow(
                            ParseFile.run,
                            str(new_file["id"]),
                        )
                        await self.increase(increase)
                else:
                    await self.increase(80)
            elif file2.filetype in BASE_FILETYPE_PARSING_MAP:
                updated_filetype = await workflow.execute_activity(
                    BASE_FILETYPE_PARSING_MAP[file2.filetype],
                    file,
                    schedule_to_close_timeout=timedelta(seconds=1200),
                )
                await self.increase(10)
                if updated_filetype and updated_filetype != file2.filetype:
                    file2.filetype = updated_filetype
                    await workflow.execute_activity(
                        activities.update_filetype,
                        file2,
                        schedule_to_close_timeout=timedelta(seconds=1200),
                    )
                    await workflow.execute_child_workflow(ParseFile.run, str(file2.id))
                else:
                    await self.increase(70)
            else:
                await self.increase(80)
            log.info(f"Completed file: {file_id}")
        finally:
            await self.delete_bar()


@workflow.defn(sandboxed=False)
class LabelProcesses:

    @workflow.run
    async def run(self, label: schemas.LabelProcess) -> None:
        await workflow.execute_activity(
            activities.label_processes,
            label,
            schedule_to_close_timeout=timedelta(seconds=1200),
        )


@workflow.defn(sandboxed=False)
class MarkDead:

    @workflow.run
    async def run(self) -> None:
        await workflow.execute_activity(
            activities.mark_dead,
            schedule_to_close_timeout=timedelta(seconds=120),
        )


@workflow.defn(sandboxed=False)
class CreateTimeline:

    @workflow.run
    async def run(self, timeline: schemas.CreateTimeline) -> None:
        await workflow.execute_activity(
            activities.summarize_c2_tasks,
            schedule_to_close_timeout=timedelta(hours=1),
        )

        await workflow.execute_activity(
            activities.summarize_socks_tasks,
            schedule_to_close_timeout=timedelta(hours=1),
        )

        await workflow.execute_activity(
            activities.summarize_manual_tasks,
            schedule_to_close_timeout=timedelta(hours=1),
        )

        await workflow.execute_activity(
            activities.create_timeline,
            timeline,
            schedule_to_close_timeout=timedelta(hours=2),
        )


@workflow.defn(sandboxed=False)
class TextParser:

    @workflow.run
    async def run(self, output: schemas.TextParse) -> None:
        await workflow.execute_activity(
            activities.parse_output,
            output,
            schedule_to_close_timeout=timedelta(seconds=120),
        )


@workflow.defn(sandboxed=False, name="UpdateSocksServer")
class UpdateSocksServer:

    @workflow.run
    async def run(self, socks_server: schemas.SocksServerCreate) -> None:
        await workflow.execute_activity(
            activities.update_socks_server,
            socks_server,
            schedule_to_close_timeout=timedelta(seconds=120),
        )


@workflow.defn(sandboxed=False, name="C2ConnectorWorkflow")
class C2ConnectorWorkflow:

    @workflow.run
    async def run(self, c2_server_id: str) -> schemas.C2ServerAll | None:
        result = await workflow.execute_activity(
            activities.get_server_settings,
            c2_server_id,
            schedule_to_close_timeout=timedelta(hours=1),
        )
        return result


@workflow.defn(sandboxed=False)
class SyncAll:

    @workflow.run
    async def run(self, c2_server_id: str) -> None:
        queue = f"{c2_server_id}_jobs"
        await workflow.execute_activity(
            "sync_all",
            task_queue=queue,
            schedule_to_close_timeout=timedelta(hours=1),
        )


@workflow.defn(sandboxed=False, name="C2ConnectorDataWorkflow")
class C2ConnectorDataWorkflow:

    def __init__(self) -> None:
        self.implant_queue: asyncio.Queue[schemas.C2ImplantCreate] = asyncio.Queue()
        self.task_queue: asyncio.Queue[schemas.C2TaskCreate] = asyncio.Queue()
        self.task_output_queue: asyncio.Queue[schemas.C2OutputCreate] = asyncio.Queue()
        self.proxy_queue: asyncio.Queue[schemas.ProxyCreate] = asyncio.Queue()
        self.c2_task_status_queue: asyncio.Queue[schemas.C2TaskStatus] = asyncio.Queue()
        self.file_queue: asyncio.Queue[schemas.FileCreate] = asyncio.Queue()
        self._exit = False

    @workflow.run
    async def run(
        self, c2_connector: schemas.C2Connector
    ) -> schemas.C2ServerAll | None:
        await workflow.execute_activity(
            activities.update_c2_server_status,
            schemas.C2ServerStatusUpdate(
                c2_server_id=c2_connector.c2_server_id,
                status=schemas.C2ServerStatus(
                    status=schemas.Status.running,
                    name=c2_connector.name,
                ),
            ),
            schedule_to_close_timeout=timedelta(minutes=2),
        )

        counter = 0
        while True:
            await workflow.wait_condition(
                lambda: not self.implant_queue.empty()
                or not self.task_queue.empty()
                or not self.task_output_queue.empty()
                or not self.proxy_queue.empty()
                or not self.c2_task_status_queue.empty()
                or not self.file_queue.empty()
                or self._exit,
            )
            while not self.implant_queue.empty():
                c2_implant = self.implant_queue.get_nowait()
                c2_implant.c2_server_id = c2_connector.c2_server_id
                await workflow.execute_activity(
                    activities.save_implant,
                    c2_implant,
                    schedule_to_close_timeout=timedelta(seconds=120),
                )
                counter += 1
            while not self.task_queue.empty():
                c2_task = self.task_queue.get_nowait()
                c2_task.c2_server_id = c2_connector.c2_server_id
                await workflow.execute_activity(
                    activities.save_task,
                    c2_task,
                    schedule_to_close_timeout=timedelta(seconds=120),
                )
                counter += 1
            while not self.task_output_queue.empty():
                c2_task_output = self.task_output_queue.get_nowait()
                c2_task_output.c2_server_id = c2_connector.c2_server_id
                output_created = await workflow.execute_activity(
                    activities.save_task_output,
                    c2_task_output,
                    schedule_to_close_timeout=timedelta(seconds=120),
                )
                counter += 1
                if output_created.created:
                    if output_created.highest_process_number:
                        await workflow.start_child_workflow(
                            LabelProcesses.run,
                            schemas.LabelProcess(
                                host_id=str(output_created.host_id),
                                number=output_created.highest_process_number,
                            ),
                            parent_close_policy=workflow.ParentClosePolicy.ABANDON,
                        )
                    else:
                        await workflow.start_child_workflow(
                            TextParser.run,
                            schemas.TextParse(
                                text=output_created.output,
                                c2_implant_id=output_created.c2_implant_id,
                                c2_output_id=output_created.c2_output_id,
                            ),
                            task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
                            parent_close_policy=workflow.ParentClosePolicy.ABANDON,
                        )
            while not self.proxy_queue.empty():
                proxy = self.proxy_queue.get_nowait()
                proxy.c2_server_id = c2_connector.c2_server_id
                await workflow.execute_activity(
                    activities.save_proxy,
                    proxy,
                    schedule_to_close_timeout=timedelta(seconds=120),
                )
                counter += 1
            while not self.c2_task_status_queue.empty():
                c2_task_status = self.c2_task_status_queue.get_nowait()
                await workflow.execute_activity(
                    activities.update_c2_task_status,
                    c2_task_status,
                    schedule_to_close_timeout=timedelta(seconds=120),
                )
                counter += 1
            while not self.file_queue.empty():
                file = self.file_queue.get_nowait()
                file.c2_server_id = c2_connector.c2_server_id
                file_db = await workflow.execute_activity(
                    activities.save_file,
                    file,
                    schedule_to_close_timeout=timedelta(seconds=120),
                )
                counter += 1
                if file_db:
                    await workflow.start_child_workflow(
                        ParseFile.run,
                        str(file_db.id),
                        task_queue=constants.WORKER_TASK_QUEUE,
                        parent_close_policy=workflow.ParentClosePolicy.ABANDON,
                    )
            if self._exit:
                break
            if counter > 100:
                workflow.continue_as_new(c2_connector)

        log.info(f"C2ConnectorDataWorkflow finished for {c2_connector.c2_server_id}")
        await workflow.execute_activity(
            activities.update_c2_server_status,
            schemas.C2ServerStatusUpdate(
                c2_server_id=c2_connector.c2_server_id,
                status=schemas.C2ServerStatus(
                    status=schemas.Status.exited,
                    name=c2_connector.name,
                ),
            ),
            schedule_to_close_timeout=timedelta(minutes=2),
        )

    @workflow.signal(name="save_implant")
    async def save_implant(self, c2_implant: schemas.C2ImplantCreate):
        self.implant_queue.put_nowait(c2_implant)

    @workflow.signal(name="save_proxy")
    async def save_proxy(self, proxy: schemas.ProxyCreate):
        self.proxy_queue.put_nowait(proxy)

    @workflow.signal(name="save_file")
    async def save_file(self, file: schemas.FileCreate) -> None:
        self.file_queue.put_nowait(file)

    @workflow.signal(name="c2_task_status")
    async def c2_task_status(self, c2_task_status: schemas.C2TaskStatus) -> None:
        self.c2_task_status_queue.put_nowait(c2_task_status)

    @workflow.update(name="get_settings")
    async def get_settings(self, c2_server_id: str) -> schemas.C2ServerAll | None:
        return await workflow.execute_activity(
            activities.get_server_settings,
            c2_server_id,
            schedule_to_close_timeout=timedelta(seconds=120),
        )

    @workflow.signal(name="save_task")
    async def save_task(self, c2_task: schemas.C2TaskCreate):
        self.task_queue.put_nowait(c2_task)

    @workflow.signal(name="save_task_output")
    async def save_task_output(self, c2_task_output: schemas.C2OutputCreate) -> None:
        self.task_output_queue.put_nowait(c2_task_output)

    @workflow.signal
    def exit(self) -> None:
        self._exit = True


@workflow.defn(sandboxed=False)
class CreateSummaries:

    @workflow.run
    async def run(self) -> None:
        await workflow.execute_activity(
            activities.summarize_c2_tasks,
            schedule_to_close_timeout=timedelta(hours=1),
        )

        await workflow.execute_activity(
            activities.summarize_socks_tasks,
            schedule_to_close_timeout=timedelta(hours=1),
        )

        await workflow.execute_activity(
            activities.summarize_manual_tasks,
            schedule_to_close_timeout=timedelta(hours=1),
        )


@workflow.defn(sandboxed=False)
class CreateC2ImplantSuggestion:

    @workflow.run
    async def run(self, req: schemas.C2ImplantSuggestionRequest) -> None:
        await workflow.execute_activity(
            activities.create_c2_implant_suggestion,
            req,
            schedule_to_close_timeout=timedelta(hours=1),
        )


@workflow.defn(sandboxed=False)
class CreateDomainSuggestion:

    @workflow.run
    async def run(self, req: schemas.SuggestionsRequest) -> None:
        await workflow.execute_activity(
            activities.create_domain_suggestion,
            req,
            schedule_to_close_timeout=timedelta(hours=1),
        )


@workflow.defn(sandboxed=False)
class CreateChecklist:

    @workflow.run
    async def run(self, req: schemas.SuggestionsRequest) -> None:
        await workflow.execute_activity(
            activities.create_domain_checklist,
            req,
            schedule_to_close_timeout=timedelta(hours=1),
        )


@workflow.defn(sandboxed=False)
class CreateFileSuggestion:

    @workflow.run
    async def run(self, req: schemas.SuggestionsRequest) -> None:
        await workflow.execute_activity(
            activities.create_share_list_suggestion,
            req,
            schedule_to_close_timeout=timedelta(hours=1),
        )

        await workflow.execute_activity(
            activities.create_share_root_list_suggestion,
            req,
            schedule_to_close_timeout=timedelta(hours=1),
        )

        await workflow.execute_activity(
            activities.create_file_download_suggestion,
            req,
            schedule_to_close_timeout=timedelta(hours=1),
        )

        await workflow.execute_activity(
            activities.create_dir_ls_suggestion,
            req,
            schedule_to_close_timeout=timedelta(hours=1),
        )


@workflow.defn(sandboxed=False)
class PlaybookDetectionRisk:

    async def c2_job_detection_risk(self, req: schemas.C2JobDetectionRiskRequest) -> None:
        await workflow.execute_activity(
            activities.c2_job_detection_risk,
            req,
            schedule_to_close_timeout=timedelta(hours=1),
        )

    @workflow.run
    async def run(self, req: schemas.PlaybookDetectionRiskSuggestion) -> None:
        steps: list[schemas.ChainStep] = await workflow.execute_activity(
            activities.get_playbook_steps,
            req.playbook_id,
            schedule_to_close_timeout=timedelta(seconds=5),
        )
        for step in steps:
            if step.c2_job_id:
                c2_req  = schemas.C2JobDetectionRiskRequest(
                    additional_prompt=req.additional_prompt,
                    c2_job_id=step.c2_job_id,
                )
                # tg.start_soon(self.c2_job_detection_risk, c2_req)
                await self.c2_job_detection_risk(c2_req)


@workflow.defn(sandboxed=False)
class PrivEscSuggestions:

    @workflow.run
    async def run(self, req: schemas.SuggestionsRequest) -> None:
        await workflow.execute_activity(
            activities.kerberoasting_suggestions,
            req,
            schedule_to_close_timeout=timedelta(hours=1),
        )
