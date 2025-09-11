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

from temporalio import workflow
from datetime import timedelta
import structlog
from harbinger.connectors import activities


from harbinger import schemas

log = structlog.get_logger()


@workflow.defn(sandboxed=False)
class C2ServerCommand:
    @workflow.run
    async def run(self, server_command: schemas.C2ServerCommand) -> None:
        activity = None
        if server_command.command == schemas.Command.start:
            log.info(f"Starting container for {server_command.id}")
            activity = activities.start
        elif server_command.command == schemas.Command.stop:
            log.info(f"Stopping container for {server_command.id}")
            activity = activities.stop
        elif server_command.command == schemas.Command.restart:
            log.info(f"Restart container for {server_command.id}")
            activity = activities.restart
        elif server_command.command == schemas.Command.create:
            log.info(f"Creating container for {server_command.id}")
            activity = activities.create
        elif server_command.command == schemas.Command.delete:
            log.info(f"Deleting container for {server_command.id}")
            activity = activities.delete
        if activity:
            await workflow.execute_activity(
                activity,
                server_command,
                schedule_to_close_timeout=timedelta(hours=1),
            )


@workflow.defn(sandboxed=False)
class C2ServerLoop:
    @workflow.run
    async def run(self) -> None:
        await workflow.execute_activity(
            activities.loop,
            schedule_to_close_timeout=timedelta(minutes=5),
        )
