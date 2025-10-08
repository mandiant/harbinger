import httpx
import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_get_dynamic_settings(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/settings/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
