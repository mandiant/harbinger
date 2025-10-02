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

# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest.mock import AsyncMock, patch

import httpx
import pytest

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


async def test_healthcheck_success(client: httpx.AsyncClient):
    """Tests that the healthcheck endpoint returns 200 when all services are healthy."""
    with (
        patch("harbinger.api.v1.endpoints.healthcheck.redis.ping", new_callable=AsyncMock) as mock_redis_ping,
        patch("sqlalchemy.ext.asyncio.AsyncSession.execute", new_callable=AsyncMock) as mock_db_execute,
    ):
        mock_redis_ping.return_value = True
        mock_db_execute.return_value = None
        response = await client.get("/healthcheck")
        assert response.status_code == 200
        assert response.json() == {"database": "ok", "redis": "ok"}


async def test_healthcheck_db_error(client: httpx.AsyncClient):
    """Tests that the healthcheck endpoint returns 503 when the database is down."""
    with (
        patch("harbinger.api.v1.endpoints.healthcheck.redis.ping", new_callable=AsyncMock) as mock_redis_ping,
        patch("sqlalchemy.ext.asyncio.AsyncSession.execute", new_callable=AsyncMock) as mock_db_execute,
    ):
        mock_redis_ping.return_value = True
        mock_db_execute.side_effect = Exception("DB error")
        response = await client.get("/healthcheck")
        assert response.status_code == 503
        assert response.json() == {"detail": {"database": "error", "redis": "ok"}}


async def test_healthcheck_redis_error(client: httpx.AsyncClient):
    """Tests that the healthcheck endpoint returns 503 when redis is down."""
    with (
        patch("harbinger.api.v1.endpoints.healthcheck.redis.ping", new_callable=AsyncMock) as mock_redis_ping,
        patch("sqlalchemy.ext.asyncio.AsyncSession.execute", new_callable=AsyncMock) as mock_db_execute,
    ):
        mock_redis_ping.side_effect = Exception("Redis error")
        mock_db_execute.return_value = None
        response = await client.get("/healthcheck")
        assert response.status_code == 503
        assert response.json() == {"detail": {"database": "ok", "redis": "error"}}


async def test_healthcheck_all_error(client: httpx.AsyncClient):
    """Tests that the healthcheck endpoint returns 503 when all services are down."""
    with (
        patch("harbinger.api.v1.endpoints.healthcheck.redis.ping", new_callable=AsyncMock) as mock_redis_ping,
        patch("sqlalchemy.ext.asyncio.AsyncSession.execute", new_callable=AsyncMock) as mock_db_execute,
    ):
        mock_redis_ping.side_effect = Exception("Redis error")
        mock_db_execute.side_effect = Exception("DB error")
        response = await client.get("/healthcheck")
        assert response.status_code == 503
        assert response.json() == {"detail": {"database": "error", "redis": "error"}}
