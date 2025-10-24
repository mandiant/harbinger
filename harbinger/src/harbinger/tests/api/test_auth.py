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

import httpx
import pytest
from fastapi.routing import APIRoute
from harbinger.config.app import app

pytestmark = pytest.mark.asyncio

# A list of paths that are not protected by authentication.
# All other routes should require authentication.
# This list should be kept up-to-date with any new public routes.
# Wildcards are not supported, the full path must be specified.
PUBLIC_PATHS = {
    "/healthcheck",
    "/auth/login",
    "/auth/logout",
    "/auth/forgot-password",
    "/auth/reset-password",
    "/docs",
    "/openapi.json",
    "/redoc",
}


@pytest.mark.asyncio
async def test_all_routes_are_protected_by_authentication(client: httpx.AsyncClient, monkeypatch):
    """
    Tests that all routes are protected by authentication, except for the
    ones in the PUBLIC_PATHS list.
    """

    async def mock_get_client():
        return None

    monkeypatch.setattr("harbinger.worker.client.get_client", mock_get_client)
    unprotected_routes = []
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path not in PUBLIC_PATHS:
            for method in route.methods:
                # Skip HEAD methods as they don't return a body
                if method == "HEAD":
                    continue
                response = await client.request(method, route.path)
                if response.status_code not in [401, 405]:
                    unprotected_routes.append(f"{method} {route.path}")

    assert not unprotected_routes, f"The following routes are not protected by authentication: {unprotected_routes}"
