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

from harbinger.database import schemas
from harbinger.database.redis_pool import redis
from harbinger.config import constants
from redis.commands.json.path import Path
import harbinger.proto.v1.messages_pb2 as messages_pb2
from typing import Coroutine, Callable, Awaitable


async def get_progress_bars() -> list[schemas.ProgressBar]:
    progress_bars: set = await redis.smembers(constants.PROGRESS_BARS_SET_KEY)  # type: ignore
    result = []
    if progress_bars:
        for bar_id in progress_bars:
            redis_key = f"{constants.PROGRESS_BAR_PREFIX}{bar_id}"
            data_dict = {}
            for key, _ in schemas.ProgressBar.model_fields.items():
                data_dict[key] = await redis.get(f"{redis_key}.{key}")
            result.append(schemas.ProgressBar.model_validate(data_dict))
    return result


async def create_progress_bar(bar: schemas.ProgressBar) -> None:
    redis_key = f"{constants.PROGRESS_BAR_PREFIX}{bar.id}"
    data = bar.model_dump()
    for key, value in data.items():
        await redis.set(f"{redis_key}.{key}", value)
    await redis.sadd(constants.PROGRESS_BARS_SET_KEY, bar.id)  # type: ignore
    event = messages_pb2.Event(
        event=schemas.Event.progress, name=schemas.EventType.new, id=bar.id,
        progress=messages_pb2.Progress(
            id=bar.id,
            current=bar.current,
            max=bar.max,
            percentage=bar.percentage,
            type=bar.type,
            description=bar.description,
        )
    ).SerializeToString()
    await redis.publish(
        schemas.Streams.events,
        event,
    )


async def delete_progress_bar(bar_id: str) -> None:
    await redis.srem(constants.PROGRESS_BARS_SET_KEY, bar_id)  # type: ignore
    redis_key = f"{constants.PROGRESS_BAR_PREFIX}{bar_id}"
    for key, _ in schemas.ProgressBar.model_fields.items():
        await redis.delete(f"{redis_key}.{key}")

    event = messages_pb2.Event(
        event=schemas.Event.progress, name=schemas.EventType.deleted, id=bar_id,
        progress=messages_pb2.Progress(
            id=bar_id,
        )
    ).SerializeToString()
    await redis.publish(
        schemas.Streams.events,
        event,
    )


async def update_progress_bar(bar_id: str, current: int, percentage: float) -> None:
    redis_key = f"{constants.PROGRESS_BAR_PREFIX}{bar_id}"
    await redis.set(f"{redis_key}.current", current)
    await redis.set(f"{redis_key}.percentage", percentage)

    event = messages_pb2.Event(
        event=schemas.Event.progress, name=schemas.EventType.update, id=bar_id,
        progress=messages_pb2.Progress(
            id=bar_id,
            percentage=percentage,
            current=current,
        )
    ).SerializeToString()
    await redis.publish(
        schemas.Streams.events,
        event,
    )


class ProgressBar:
    """Object to show a progress bar for the interface"""

    def __init__(self, bar_id: str, max: int, current: int = 0, description: str = "") -> None:
        self.bar_id = bar_id
        self.max = max
        if self.max == 0:
            self.max = 1
        self.current = current
        self.description=description

    async def increment(self, step: int = 1) -> None:
        self.current += step
        await update_progress_bar(self.bar_id, self.current, self.current / self.max)

    async def __aenter__(self) -> Callable[[int], Awaitable[None]]:
        await create_progress_bar(schemas.ProgressBar(
            current=self.current,
            max=self.max,
            id=self.bar_id,
            description=self.description,
            percentage=self.current/self.max
        ))
        return self.increment
    
    async def __aexit__(self, exc_type, exc, tb) -> None:
        await update_progress_bar(self.bar_id, self.max, 1)
        await delete_progress_bar(self.bar_id)
