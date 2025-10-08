import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_list_certificate_authorities(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    ca_in = schemas.CertificateAuthorityCreate(
        ca_name="Test CA",
    )
    await crud.create_certificate_authority(db=db_session, certificate_authority=ca_in)

    response = await authenticated_client.get("/certificate_authorities/")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["ca_name"] == "Test CA"


@pytest.mark.asyncio
async def test_list_certificate_authorities_empty(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/certificate_authorities/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}


@pytest.mark.asyncio
async def test_get_certificate_authority(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    ca_in = schemas.CertificateAuthorityCreate(
        ca_name="Test CA",
    )
    _, created_ca = await crud.create_certificate_authority(db=db_session, certificate_authority=ca_in)

    response = await authenticated_client.get(f"/certificate_authorities/{created_ca.id}")

    assert response.status_code == 200
    assert response.json()["ca_name"] == "Test CA"


@pytest.mark.asyncio
async def test_get_certificate_authority_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/certificate_authorities/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_get_certificate_authorities_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/certificate_authorities/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
