import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_proxy(db_session: AsyncSession) -> schemas.Proxy:
    proxy_in = schemas.ProxyCreate(
        port=8080,
        type="socks5",
        status="connected",
    )
    proxy = await crud.create_proxy(db=db_session, proxy=proxy_in)
    return schemas.Proxy.model_validate(proxy)


@pytest.mark.asyncio
async def test_read_proxies(authenticated_client: httpx.AsyncClient, db_proxy: schemas.Proxy):
    response = await authenticated_client.get("/proxies/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_read_proxy(authenticated_client: httpx.AsyncClient, db_proxy: schemas.Proxy):
    response = await authenticated_client.get(f"/proxies/{db_proxy.id}")

    assert response.status_code == 200
    assert response.json()["status"] == db_proxy.status


@pytest.mark.asyncio
async def test_create_proxy(authenticated_client: httpx.AsyncClient):
    proxy_data = {
        "port": 8888,
        "type": "socks5",
        "status": "connected",
    }
    response = await authenticated_client.post("/proxies/", json=proxy_data)

    assert response.status_code == 200
    assert response.json()["port"] == 8888


@pytest.mark.asyncio
async def test_update_proxy(authenticated_client: httpx.AsyncClient, db_proxy: schemas.Proxy):
    update_data = {
        "port": 9999,
        "type": "socks4",
        "status": "disconnected",
    }
    response = await authenticated_client.put(f"/proxies/{db_proxy.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["port"] == 9999


@pytest.mark.asyncio
async def test_get_proxy_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/proxies/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
