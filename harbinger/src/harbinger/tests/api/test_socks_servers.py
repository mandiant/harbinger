import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_socks_server(db_session: AsyncSession) -> schemas.SocksServer:
    server_in = schemas.SocksServerCreate(
        id=uuid.uuid4(),
        type="docker",
        hostname="localhost",
        operating_system="linux",
    )
    server = await crud.create_socks_server(db=db_session, socks_server=server_in)
    return schemas.SocksServer.model_validate(server)


@pytest.mark.asyncio
async def test_list_socks_servers(authenticated_client: httpx.AsyncClient, db_socks_server: schemas.SocksServer):
    response = await authenticated_client.get("/socks_servers/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_socks_server(authenticated_client: httpx.AsyncClient, db_socks_server: schemas.SocksServer):
    response = await authenticated_client.get(f"/socks_servers/{db_socks_server.id}")

    assert response.status_code == 200
    assert response.json()["hostname"] == "localhost"


@pytest.mark.asyncio
async def test_get_socks_server_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/socks_servers/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
