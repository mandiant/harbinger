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

"""
Temporal Workflow and Activities for the Plan Supervisor.

This module contains the core Temporal workflow, activities, and helper
functions for the Plan Supervisor agent. It is responsible for managing the
lifecycle of penetration testing plans, reacting to events from a Redis
stream, and using an LLM to generate and update plan steps.
"""

import asyncio
import json
import uuid
from datetime import timedelta
from typing import List

import rigging as rg
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio import activity, workflow
from temporalio.exceptions import ApplicationError

from harbinger.database import crud, filters, schemas
from harbinger.database.database import SessionLocal
from harbinger.database.redis_pool import redis
from harbinger.enums import LlmStatus
from harbinger.worker import activities
from harbinger.worker.genai import prompts, tools

log = structlog.get_logger()


# --- Helper Functions (Consolidated from supervisor.py) ---


def format_plan_for_llm(
    plan: schemas.Plan,
    steps: list[schemas.PlanStep],
    suggestions: list[schemas.Suggestion],
) -> str:
    """
    Formats the plan, its steps, and any existing suggestions into a
    concise, readable string for the LLM.
    """
    summary = f"Plan Name: {plan.name}\n"
    if plan.objective:
        summary += f"Overall Objective: {plan.objective}\n"
    summary += "\n"

    if not steps:
        summary += "The current plan has no steps."
        return summary

    suggestions_by_step: dict[uuid.UUID | str, list[schemas.Suggestion]] = {}
    for s in suggestions:
        if s.plan_step_id:
            suggestions_by_step.setdefault(s.plan_step_id, []).append(s)

    summary += "Current Plan Steps:\n"
    sorted_steps = sorted(steps, key=lambda s: s.order)

    for step in sorted_steps:
        summary += (
            f"- ID: {step.id}, Order: {step.order}, Status: {step.status}, "
            f"Description: {step.description}, Notes: {step.notes}\n"
        )
        if step.id in suggestions_by_step:
            summary += "  Existing Suggestions for this step:\n"
            for s in suggestions_by_step[step.id]:
                args_str = json.dumps(s.arguments, default=str)
                summary += f"    - Suggestion ID: {s.id}, Name: '{s.name}', Reason: {s.reason}, Arguments: {args_str}\n"
    return summary


async def get_database_summary(db: AsyncSession) -> str:
    """Gathers key statistics from the database to form a summary string."""
    stats = await crud.get_database_statistics(db)
    summary_parts = [f"{count} {name}" for name, count in stats.items()]
    return "Database State Summary: " + ", ".join(summary_parts) + "."


# --- Tool Definitions (Consolidated from supervisor.py) ---

SUPERVISOR_TOOLS: List[rg.Tool] = [
    tools.get_all_c2_implant_info,
    tools.get_c2_tasks_executed,
    tools.get_playbooks,
    tools.get_playbook_templates,
    tools.get_proxies_info,
    tools.get_previous_suggestions,
    tools.get_socks_servers_info,
    tools.get_credentials_info,
    tools.get_situational_awareness_info,
    tools.get_domains_info,
    tools.get_undownloaded_share_files,
    tools.get_unindexed_share_folders,
    tools.get_hosts,
    tools.get_network_shares,
    tools.list_filters,
    tools.create_suggestion_for_plan_step,
    tools.create_plan_step,
    tools.update_plan_step,
]


# --- Activities ---


@activity.defn
async def create_consumer_group_activity(plan_id: str) -> None:
    """Creates a unique Redis consumer group for the plan if it doesn't exist."""
    stream_name = "supervisor:events"
    group_name = f"supervisor:group:{plan_id}"
    try:
        await redis.xgroup_create(stream_name, group_name, mkstream=True)
        log.info(
            "Created Redis consumer group",
            group_name=group_name,
            stream_name=stream_name,
        )
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            log.error("Failed to create consumer group", error=e)
            raise


@activity.defn
async def poll_for_stream_events_activity(plan_id: str) -> list[str]:
    """
    Polls the Redis stream and drains all pending events for this plan's
    consumer group in a single batch.
    """
    stream_name = "supervisor:events"
    group_name = f"supervisor:group:{plan_id}"
    consumer_name = f"consumer:{plan_id}"

    all_events_in_batch = []

    # Loop to drain all currently available messages
    while True:
        try:
            events = await redis.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={stream_name: ">"},
                count=10,  # Read up to 10 at a time
                block=200,  # Short block time
            )

            if not events:
                break  # No more events in the stream

            message_ids_to_ack = []
            for _, messages in events:
                for message_id, message_data in messages:
                    # The redis client automatically decodes keys and values to strings
                    if "payload" in message_data:
                        payload = message_data["payload"].strip()
                        if payload:
                            all_events_in_batch.append(payload)
                    message_ids_to_ack.append(message_id)

            if message_ids_to_ack:
                await redis.xack(stream_name, group_name, *message_ids_to_ack)

        except Exception as e:
            log.error(
                "Error polling or processing stream events in activity loop", error=e
            )
            # Break the loop on error to avoid getting stuck
            break

    log.info("Returning processed events", count=len(all_events_in_batch))
    return all_events_in_batch


@activity.defn
async def generate_initial_steps_activity(plan_id: str) -> None:
    """Generates the initial high-level steps for a plan if they do not already exist."""
    plan_uuid = uuid.UUID(plan_id)
    async with SessionLocal() as db:
        existing_steps = await crud.get_plan_steps(
            db, filters=filters.PlanStepFilter(plan_id=plan_uuid), limit=1
        )
        if existing_steps:
            log.info("Plan steps already exist. Skipping generation.", plan_id=plan_id)
            return

        plan = await crud.get_plan(db, id=plan_uuid)
        if not plan:
            raise ApplicationError(f"Plan with ID {plan_id} not found.")

        # Create a detailed objective string for the LLM
        llm_objectives = f"Plan Name: {plan.name}"
        if plan.objective:
            llm_objectives += f"\nOverall Objective: {plan.objective}"

        pipeline = prompts.generator.chat().using(SUPERVISOR_TOOLS, max_depth=100)
        run = prompts.generate_testing_plan.bind(pipeline)
        generated_plan: prompts.GeneratedPlan = await run(
            objectives=llm_objectives,
            current_state=await get_database_summary(db),
        )
        if generated_plan.steps:
            log.info(
                "LLM generated initial steps",
                count=len(generated_plan.steps),
                plan_id=plan_id,
            )
            for step in generated_plan.steps:
                await crud.create_plan_step(
                    db, schemas.PlanStepCreate(**step.model_dump(), plan_id=plan_uuid)
                )
        else:
            log.warning("LLM did not generate any initial steps", plan_id=plan_id)



@activity.defn
async def handle_events_activity(plan_id: str, events: list[str]) -> None:
    """Handles a batch of events by invoking the LLM to update the plan."""
    if not events:
        return
    log.info(f"handle_events_activity, number of events: {len(events)}", plan_id=plan_id)
    plan_uuid = uuid.UUID(plan_id)
    aggregated_event_context = "\n".join(events)

    async with SessionLocal() as db:
        plan_obj = await crud.get_plan(db, id=plan_uuid)
        if not plan_obj:
            raise ApplicationError(f"Plan with ID {plan_id} not found.")

        plan_steps = await crud.get_plan_steps(
            db, filters=filters.PlanStepFilter(plan_id=plan_uuid), limit=1000
        )
        plan_step_ids = [step.id for step in plan_steps]
        suggestions = []
        if plan_step_ids:
            suggestions = await crud.get_suggestions(
                db,
                filters=filters.SuggestionFilter(
                    plan_step=filters.PlanStepFilter(id__in=plan_step_ids)
                ),
                limit=1000,
            )

        plan_summary = format_plan_for_llm(
            schemas.Plan.model_validate(plan_obj), list(plan_steps), list(suggestions)
        )
        event_text = (
            f"{await get_database_summary(db)}. New events:\n{aggregated_event_context}"
        )

        pipeline = prompts.generator.chat().using(SUPERVISOR_TOOLS, max_depth=100)
        run = prompts.update_testing_plan.bind(pipeline)
        llm_response: prompts.SupervisorSummary = await run(
            current_plan_summary=plan_summary, new_event=event_text
        )
        log.info(
            "LLM processed event batch",
            plan_id=plan_id,
            summary=llm_response.summary_text,
            event_count=len(events),
        )


# --- Workflow ---


@workflow.defn(sandboxed=False)
class PlanSupervisorWorkflow:
    def __init__(self):
        self._should_stop = False
        self._force_update_requested = False

    async def _process_events(self, plan_id: str) -> None:
        """Helper to poll for and handle a batch of events."""
        log.info("Polling for stream events.", plan_id=plan_id)
        all_events_in_batch = await workflow.execute_activity(
            poll_for_stream_events_activity,
            plan_id,
            start_to_close_timeout=timedelta(minutes=1),
        )

        log.info(f"Found {len(all_events_in_batch)} events in batch.", plan_id=plan_id)

        if all_events_in_batch:
            await workflow.execute_activity(
                activities.set_plan_status_activity,
                args=[plan_id, LlmStatus.PROCESSING],
                start_to_close_timeout=timedelta(minutes=1),
            )
            await workflow.execute_activity(
                handle_events_activity,
                args=[plan_id, all_events_in_batch],
                start_to_close_timeout=timedelta(minutes=10),
            )
            await workflow.execute_activity(
                activities.set_plan_status_activity,
                args=[plan_id, LlmStatus.MONITORING],
                start_to_close_timeout=timedelta(minutes=1),
            )

            # After processing events, check if the plan is complete.
            is_plan_completed = await workflow.execute_activity(
                activities.check_and_finalize_plan_activity,
                plan_id,
                start_to_close_timeout=timedelta(minutes=1),
            )
            if is_plan_completed:
                log.info(
                    "Plan has been completed, stopping workflow.", plan_id=plan_id
                )
                self._should_stop = True

        else:
            log.info("No new events, skipping update step.", plan_id=plan_id)

    @workflow.run
    async def run(self, plan_id: str) -> None:
        """Main workflow execution logic with event batching."""
        batching_interval_seconds = 60

        try:
            # Set initial status to MONITORING
            await workflow.execute_activity(
                activities.set_plan_status_activity,
                args=[plan_id, LlmStatus.MONITORING],
                start_to_close_timeout=timedelta(minutes=1),
            )
            await workflow.execute_activity(
                create_consumer_group_activity,
                plan_id,
                start_to_close_timeout=timedelta(minutes=1),
            )

            # Generate initial steps if needed
            await workflow.execute_activity(
                activities.set_plan_status_activity,
                args=[plan_id, LlmStatus.PROCESSING],
                start_to_close_timeout=timedelta(minutes=1),
            )
            await workflow.execute_activity(
                generate_initial_steps_activity,
                plan_id,
                start_to_close_timeout=timedelta(minutes=5),
            )
            await workflow.execute_activity(
                activities.set_plan_status_activity,
                args=[plan_id, LlmStatus.MONITORING],
                start_to_close_timeout=timedelta(minutes=1),
            )

            # --- Immediately analyze the newly created plan to generate the first suggestions ---
            log.info("Performing initial analysis of the new plan.", plan_id=plan_id)
            await workflow.execute_activity(
                activities.set_plan_status_activity,
                args=[plan_id, LlmStatus.PROCESSING],
                start_to_close_timeout=timedelta(minutes=1),
            )
            await workflow.execute_activity(
                handle_events_activity,
                args=[
                    plan_id,
                    [
                        "The initial plan has been created. Please analyze the current state and suggest the first logical action."
                    ],
                ],
                start_to_close_timeout=timedelta(minutes=10),
            )
            await workflow.execute_activity(
                activities.set_plan_status_activity,
                args=[plan_id, LlmStatus.MONITORING],
                start_to_close_timeout=timedelta(minutes=1),
            )
            # ------------------------------------------------------------------------------------

            # --- Immediate first run on startup/resume ---
            log.info(
                "Performing initial event processing cycle on startup/resume.",
                plan_id=plan_id,
            )
            await self._process_events(plan_id)
            # ---------------------------------------------

            while not self._should_stop:
                # Wait for the batching interval OR until a force_update or stop signal is received
                try:
                    await workflow.wait_condition(
                        lambda: self._force_update_requested or self._should_stop,
                        timeout=timedelta(seconds=batching_interval_seconds),
                    )
                except asyncio.TimeoutError:
                    log.info(
                        "Batching timer expired, starting processing cycle.",
                        plan_id=plan_id,
                    )
                    pass  # This is the expected timeout for our batching window

                if self._force_update_requested:
                    log.info(
                        "Force update signal received, starting processing cycle.",
                        plan_id=plan_id,
                    )

                if self._should_stop:
                    log.info(
                        "Stop signal received, terminating workflow.", plan_id=plan_id
                    )
                    break

                self._force_update_requested = False  # Reset the flag after waking up

                await self._process_events(plan_id)

        except asyncio.CancelledError:
            # This error is raised when the worker is shutting down.
            # We re-raise it to ensure the workflow is properly suspended
            # and can be resumed by another worker.
            log.warning(
                "Workflow execution was cancelled (likely due to worker shutdown).",
                plan_id=plan_id,
            )
            raise
        except Exception as e:
            # For any other unexpected exception, log the error and set the
            # plan to INACTIVE as a safety measure.
            log.error(
                "Workflow failed with an unexpected exception.",
                plan_id=plan_id,
                error=e,
            )
            await workflow.execute_activity(
                activities.set_plan_status_activity,
                args=[plan_id, LlmStatus.INACTIVE],
                start_to_close_timeout=timedelta(minutes=1),
            )
            raise
        finally:
            # This block will run ONLY when the workflow loop is exited cleanly,
            # which means the _should_stop flag was set by the stop() signal.
            if self._should_stop:
                log.info(
                    "Workflow has finished cleanly. Setting status to INACTIVE.",
                    plan_id=plan_id,
                )
                await workflow.execute_activity(
                    activities.set_plan_status_activity,
                    args=[plan_id, LlmStatus.INACTIVE],
                    start_to_close_timeout=timedelta(minutes=1),
                )

    @workflow.signal
    async def stop(self) -> None:
        self._should_stop = True

    @workflow.signal
    async def force_update(self) -> None:
        self._force_update_requested = True
        