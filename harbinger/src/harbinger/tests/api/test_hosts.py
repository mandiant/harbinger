import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_host(db_session: AsyncSession) -> schemas.Host:
    _, host = await crud.get_or_create_host(db_session, "TESTHOST")
    return schemas.Host.model_validate(host)


@pytest.mark.asyncio
async def test_get_hosts(authenticated_client: httpx.AsyncClient, db_host: schemas.Host):
    response = await authenticated_client.get("/hosts/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_host(authenticated_client: httpx.AsyncClient, db_host: schemas.Host):
    response = await authenticated_client.get(f"/hosts/{db_host.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "TESTHOST"


@pytest.mark.asyncio
async def test_get_host_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/hosts/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_modify_host(authenticated_client: httpx.AsyncClient, db_host: schemas.Host):
    update_data = {
        "objectid": "UPDATEDHOST",
        "ip_address": "127.0.0.2",
    }
    response = await authenticated_client.put(f"/hosts/{db_host.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["objectid"] == "UPDATEDHOST"


@pytest.mark.asyncio
async def test_get_host_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/hosts/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
