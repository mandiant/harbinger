import httpx
import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_get_implant_statistics(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/statistics/implant/")
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_get_job_statistics(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/statistics/job/")
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_get_server_statistics(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/statistics/server/")
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_get_share_statistics(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/statistics/share/")
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_get_sa_statistics(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/statistics/sa/")
    assert response.status_code == 200
    assert "items" in response.json()
