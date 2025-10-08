import httpx
import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_read_graph_users(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/graph/users/")
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_read_graph_groups(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/graph/groups/")
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_read_graph_computers(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/graph/computers/")
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_read_domain_controllers(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/graph/domain_controllers/")
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_mark_owned(authenticated_client: httpx.AsyncClient):
    # This test depends on having data in the graph.
    # For now, we'll just test the endpoint.
    data = {"names": ["USER@DOMAIN"]}
    response = await authenticated_client.post("/graph/mark_owned", json=data)
    assert response.status_code == 200
    assert "count" in response.json()


@pytest.mark.asyncio
async def test_get_stats(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/graph/stats/")
    assert response.status_code == 200
    assert "items" in response.json()


@pytest.mark.asyncio
async def test_get_pre_defined_queries(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/graph/pre-defined-queries/")
    assert response.status_code == 200
    assert "items" in response.json()
