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

import json  # Import json for serialization
from harbinger import schemas
from harbinger.database.redis_pool import redis
from harbinger.config import constants
from typing import Callable, Awaitable

GLOBAL_REDIS_EVENTS_CHANNEL = schemas.Streams.events


async def get_progress_bars() -> list[schemas.ProgressBar]:
    progress_bars: set = await redis.smembers(constants.PROGRESS_BARS_SET_KEY)  # type: ignore
    result = []
    if progress_bars:
        for bar_id in progress_bars:
            redis_key = f"{constants.PROGRESS_BAR_PREFIX}{bar_id}"
            # Fetch all fields to reconstruct the ProgressBar object
            bar_data = {}
            for field_name, _ in schemas.ProgressBar.model_fields.items():
                value = await redis.get(f"{redis_key}.{field_name}")
                if value is not None:
                    # Attempt to convert to correct type, as redis.get returns string/bytes
                    if field_name in ["current", "max"]:
                        bar_data[field_name] = int(value)
                    elif field_name == "percentage":
                        bar_data[field_name] = float(value)
                    else:  # id, type, description
                        bar_data[field_name] = (
                            value.decode("utf-8") if isinstance(value, bytes) else value
                        )

            # Ensure all required fields are present with defaults if necessary
            # or handle missing data appropriately.
            try:
                progress_bar_obj = schemas.ProgressBar.model_validate(bar_data)
                result.append(progress_bar_obj)
            except Exception as e:
                print(
                    f"Warning: Failed to validate ProgressBar from Redis for ID {bar_id}: {e}"
                )
                # Optionally, clean up inconsistent data in Redis here
    return result


async def create_progress_bar(bar: schemas.ProgressBar) -> None:
    redis_key = f"{constants.PROGRESS_BAR_PREFIX}{bar.id}"
    data = bar.model_dump()

    # Store fields individually in Redis
    for key, value in data.items():
        if (
            value is not None
        ):  # Ensure None values are not stored directly if not desired
            await redis.set(
                f"{redis_key}.{key}", str(value)
            )  # Convert all to string for Redis SET

    await redis.sadd(constants.PROGRESS_BARS_SET_KEY, bar.id)  # type: ignore

    # Create the event payload in the expected JSON format
    event_payload = {
        "channel": f"progress_bars.insert",  # Original channel info
        "table_name": "progress_bars",
        "operation": "insert",
        "before": None,  # No 'before' state for insert
        "after": bar.model_dump(
            mode="json"
        ),  # Convert Pydantic object to JSON-compatible dict
    }

    # Publish the JSON string to Redis
    await redis.publish(
        GLOBAL_REDIS_EVENTS_CHANNEL,
        json.dumps(event_payload),
    )


async def delete_progress_bar(bar_id: str) -> None:
    # First, retrieve the object if you need its 'before' state for the event
    # (Important for 'delete' operations in the new event structure)
    deleted_bar: schemas.ProgressBar | None = None
    existing_data = {}
    redis_key = f"{constants.PROGRESS_BAR_PREFIX}{bar_id}"
    for field_name, _ in schemas.ProgressBar.model_fields.items():
        value = await redis.get(f"{redis_key}.{field_name}")
        if value is not None:
            if field_name in ["current", "max"]:
                existing_data[field_name] = int(value)
            elif field_name == "percentage":
                existing_data[field_name] = float(value)
            else:
                existing_data[field_name] = (
                    value.decode("utf-8") if isinstance(value, bytes) else value
                )
    try:
        deleted_bar = schemas.ProgressBar.model_validate(existing_data)
    except Exception:
        # Log if validation fails, but proceed with deletion and event if possible
        print(
            f"Warning: Could not fully retrieve ProgressBar for 'before' state during deletion for ID {bar_id}"
        )

    await redis.srem(constants.PROGRESS_BARS_SET_KEY, bar_id)  # type: ignore
    for key, _ in schemas.ProgressBar.model_fields.items():
        await redis.delete(f"{redis_key}.{key}")

    # Create the event payload
    event_payload = {
        "channel": f"progress_bars.delete",
        "table_name": "progress_bars",
        "operation": "delete",
        "before": deleted_bar.model_dump(mode="json")
        if deleted_bar
        else None,  # Include 'before' state if retrieved
        "after": None,  # No 'after' state for delete
    }

    await redis.publish(
        GLOBAL_REDIS_EVENTS_CHANNEL,
        json.dumps(event_payload),
    )


async def update_progress_bar(bar_id: str, current: int, percentage: float) -> None:
    # Retrieve 'before' state for the event
    old_bar: schemas.ProgressBar | None = None
    new_bar: schemas.ProgressBar | None = None
    redis_key = f"{constants.PROGRESS_BAR_PREFIX}{bar_id}"

    existing_data = {}
    for field_name, _ in schemas.ProgressBar.model_fields.items():
        value = await redis.get(f"{redis_key}.{field_name}")
        if value is not None:
            if field_name in ["current", "max"]:
                existing_data[field_name] = int(value)
            elif field_name == "percentage":
                existing_data[field_name] = float(value)
            else:
                existing_data[field_name] = (
                    value.decode("utf-8") if isinstance(value, bytes) else value
                )
    try:
        old_bar = schemas.ProgressBar.model_validate(existing_data)
    except Exception:
        print(
            f"Warning: Could not fully retrieve old ProgressBar for 'before' state during update for ID {bar_id}"
        )

    # Perform the update in Redis
    await redis.set(f"{redis_key}.current", current)
    await redis.set(f"{redis_key}.percentage", percentage)

    # Re-retrieve 'after' state for the event
    updated_data = {}
    for field_name, _ in schemas.ProgressBar.model_fields.items():
        value = await redis.get(f"{redis_key}.{field_name}")  # Get updated values
        if value is not None:
            if field_name in ["current", "max"]:
                updated_data[field_name] = int(value)
            elif field_name == "percentage":
                updated_data[field_name] = float(value)
            else:
                updated_data[field_name] = (
                    value.decode("utf-8") if isinstance(value, bytes) else value
                )
    try:
        new_bar = schemas.ProgressBar.model_validate(updated_data)
    except Exception:
        print(
            f"Warning: Could not fully retrieve new ProgressBar for 'after' state during update for ID {bar_id}"
        )

    # Create the event payload
    event_payload = {
        "channel": f"progress_bars.update",
        "table_name": "progress_bars",
        "operation": "update",
        "before": old_bar.model_dump(mode="json")
        if old_bar
        else None,  # Include 'before' state
        "after": new_bar.model_dump(mode="json")
        if new_bar
        else None,  # Include 'after' state
    }

    await redis.publish(
        GLOBAL_REDIS_EVENTS_CHANNEL,
        json.dumps(event_payload),
    )


class ProgressBar:
    """Object to show a progress bar for the interface"""

    def __init__(
        self,
        bar_id: str,
        max: int,
        current: int = 0,
        description: str = "",
        type: str = "default",
    ) -> None:
        self.bar_id = bar_id
        self.max = max
        if self.max == 0:
            self.max = 1
        self.current = current
        self.description = description
        self.type = type  # Ensure type is initialized

    async def increment(self, step: int = 1) -> None:
        self.current += step
        # Pass the percentage directly to update_progress_bar
        await update_progress_bar(self.bar_id, self.current, self.current / self.max)

    async def __aenter__(self) -> Callable[[int], Awaitable[None]]:
        # Ensure all fields of ProgressBar are passed for creation
        progress_bar_instance = schemas.ProgressBar(
            current=self.current,
            max=self.max,
            id=self.bar_id,
            description=self.description,
            percentage=self.current / self.max,
            type=self.type,  # Ensure type is included
        )
        await create_progress_bar(progress_bar_instance)
        return self.increment

    async def __aexit__(self, exc_type, exc, tb) -> None:
        # On exit, ensure final state is pushed, then delete
        # It's good practice to send final update to max/100% before deleting
        await update_progress_bar(
            self.bar_id, self.max, 1.0
        )  # Ensure percentage is 1.0 (100%)
        await delete_progress_bar(self.bar_id)
