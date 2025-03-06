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

import contextlib
from typing import AsyncGenerator

from harbinger.config import get_settings
from neo4j import AsyncGraphDatabase, AsyncSession

settings = get_settings()


async def get_async_neo4j_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncGraphDatabase.driver(
        settings.neo4j_host, auth=(settings.neo4j_user, settings.neo4j_password)
    ) as driver:
        async with driver.session() as session:
            yield session

get_async_neo4j_session_context = contextlib.asynccontextmanager(get_async_neo4j_session)
