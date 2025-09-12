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
import contextlib
import signal

import anyio
import structlog
from rigging.logging import configure_logging
from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleAlreadyRunningError,
    ScheduleSpec,
)
from temporalio.service import RPCError
from temporalio.worker import Worker

from harbinger.config import constants
from harbinger.database.redis_pool import redis
from harbinger.worker import activities, workflows
from harbinger.worker.client import get_client
from harbinger.worker.supervisor_workflow import (
    PlanSupervisorWorkflow,
    create_consumer_group_activity,
    generate_initial_steps_activity,
    handle_events_activity,
    poll_for_stream_events_activity,
)

log = structlog.get_logger()


def cli():
    anyio.run(main)


async def main():
    configure_logging("info", "out.log", "trace")
    log.info("Starting worker")
    client = await get_client()
    file_parser = activities.FileParsing()
    worker = Worker(
        client,
        task_queue=constants.WORKER_TASK_QUEUE,
        workflows=[
            workflows.RunPlaybook,
            workflows.RunC2Job,
            workflows.MarkDead,
            workflows.LabelProcesses,
            workflows.UpdateSocksServer,
            workflows.C2ConnectorWorkflow,
            workflows.C2ConnectorDataWorkflow,
            workflows.SyncAll,
            workflows.CreateSummaries,
            workflows.CreateC2ImplantSuggestion,
            workflows.CreateDomainSuggestion,
            workflows.CreateFileSuggestion,
            workflows.PlaybookDetectionRisk,
            workflows.PrivEscSuggestions,
            workflows.GeneratePlanWorkflow,
            PlanSupervisorWorkflow,
        ],
        activities=[
            activities.get_playbook,
            activities.get_playbook_steps,
            activities.get_proxy_job,
            activities.get_c2_implant,
            activities.update_playbook_status,
            activities.update_playbook_step_status,
            activities.get_file,
            activities.update_filetype,
            activities.label_processes,
            activities.create_timeline,
            activities.mark_dead,
            activities.parse_output,
            activities.update_c2_job,
            activities.update_c2_job_status,
            activities.update_proxy_job,
            activities.update_socks_server,
            activities.get_server_settings,
            activities.save_implant,
            activities.save_task,
            activities.save_task_output,
            activities.save_proxy,
            activities.get_c2_job,
            activities.update_c2_server_status,
            activities.update_c2_task_status,
            activities.update_c2_job_c2_task_id,
            activities.save_file,
            activities.create_progress_bar,
            activities.update_progress_bar,
            activities.delete_progress_bar,
            activities.summarize_c2_tasks,
            activities.summarize_socks_tasks,
            activities.summarize_manual_tasks,
            activities.create_c2_implant_suggestion,
            activities.create_domain_suggestion,
            activities.create_file_download_suggestion,
            activities.create_dir_ls_suggestion,
            activities.create_share_list_suggestion,
            activities.kerberoasting_suggestions,
            activities.c2_job_detection_risk,
            activities.get_c2_task_output,
            activities.create_share_root_list_suggestion,
            activities.create_plan_activity,
            # Supervisor Activities
            generate_initial_steps_activity,
            handle_events_activity,
            poll_for_stream_events_activity,
            create_consumer_group_activity,
            activities.set_plan_status_activity,
            activities.check_and_finalize_plan_activity,
        ],
    )

    worker2 = Worker(
        client,
        task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
        workflows=[
            workflows.ParseFile,
            workflows.CreateTimeline,
            workflows.TextParser,
        ],
        activities=[
            activities.update_filetype,
            activities.get_file,
            file_parser.file_magic_all,
            file_parser.process_lsass,
            file_parser.process_nanodump,
            file_parser.process_pypykatz,
            file_parser.process_proces_list,
            file_parser.process_dir2json,
            file_parser.process_kdbx,
            file_parser.process_zip,
            file_parser.process_text,
            file_parser.process_json,
            file_parser.process_harbinger_zip,
            file_parser.process_harbinger_yaml,
            file_parser.process_unknown,
            file_parser.process_ccache,
            file_parser.process_ad_snapshot,
            file_parser.process_cast,
            file_parser.process_certipy_json,
            file_parser.process_certify_json,
            activities.label_processes,
            activities.create_timeline,
            activities.parse_output,
            activities.summarize_c2_tasks,
            activities.summarize_socks_tasks,
            activities.summarize_manual_tasks,
        ],
        max_concurrent_workflow_tasks=10,
        max_concurrent_activities=10,
        max_concurrent_workflow_task_polls=10,
    )
    asyncio.create_task(worker.run())
    asyncio.create_task(worker2.run())

    # delete older cron version of the loop
    handle = client.get_workflow_handle(workflow_id="markdead-loop")
    if handle:
        with contextlib.suppress(RPCError):
            await handle.terminate()

    # create new schedule based.
    with contextlib.suppress(ScheduleAlreadyRunningError):
        await client.create_schedule(
            "check-implant-states",
            Schedule(
                action=ScheduleActionStartWorkflow(
                    workflows.MarkDead.run,
                    id="check-imlant-states",
                    task_queue=constants.WORKER_TASK_QUEUE,
                ),
                spec=ScheduleSpec(
                    cron_expressions=["* * * * *"],
                ),
            ),
        )

    try:
        with anyio.open_signal_receiver(signal.SIGTERM, signal.SIGINT) as signals:
            log.info("Worker started, waiting for signal.")
            async for signum in signals:
                log.info(f"Received {signum} stopping worker")
                await worker.shutdown()
                await worker2.shutdown()
                log.info("Shutdown done!")
                break
        log.info("Done")
    finally:
        await redis.aclose()
