import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_list_domains(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    domain_in = schemas.DomainCreate(
        long_name="test.local",
        short_name="TEST",
    )
    await crud.create_domain(db=db_session, domain=domain_in)

    response = await authenticated_client.get("/domains/")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["long_name"] == "test.local"


@pytest.mark.asyncio
async def test_list_domains_empty(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/domains/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}


@pytest.mark.asyncio
async def test_get_domain(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    domain_in = schemas.DomainCreate(
        long_name="test.local",
        short_name="TEST",
    )
    created_domain = await crud.create_domain(db=db_session, domain=domain_in)

    response = await authenticated_client.get(f"/domains/{created_domain.id}")

    assert response.status_code == 200
    assert response.json()["long_name"] == "test.local"


@pytest.mark.asyncio
async def test_get_domain_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/domains/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_create_domain(authenticated_client: httpx.AsyncClient):
    domain_data = {
        "long_name": "new.local",
        "short_name": "NEW",
    }
    response = await authenticated_client.post("/domains/", json=domain_data)

    assert response.status_code == 200
    assert response.json()["long_name"] == "new.local"


@pytest.mark.asyncio
async def test_update_domain(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    domain_in = schemas.DomainCreate(
        long_name="test.local",
        short_name="TEST",
    )
    created_domain = await crud.create_domain(db=db_session, domain=domain_in)

    update_data = {
        "long_name": "updated.local",
        "short_name": "UPDATED",
    }
    response = await authenticated_client.put(f"/domains/{created_domain.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["long_name"] == "updated.local"


@pytest.mark.asyncio
async def test_get_domains_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/domains/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
