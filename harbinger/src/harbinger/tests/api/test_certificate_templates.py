import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_ca(db_session: AsyncSession) -> schemas.CertificateAuthority:
    ca_in = schemas.CertificateAuthorityCreate(
        ca_name="Test CA",
    )
    _, ca = await crud.create_certificate_authority(db=db_session, certificate_authority=ca_in)
    return ca


@pytest.mark.asyncio
async def test_get_certificate_templates(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_ca: schemas.CertificateAuthority
):
    template_in = schemas.CertificateTemplateCreate(
        template_name="Test Template",
        certificate_authorities=[db_ca.ca_name],
    )
    await crud.create_certificate_template(db=db_session, certificate_template=template_in)

    response = await authenticated_client.get("/certificate_templates/")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["template_name"] == "Test Template"


@pytest.mark.asyncio
async def test_get_certificate_templates_empty(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/certificate_templates/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}


@pytest.mark.asyncio
async def test_get_certificate_template(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_ca: schemas.CertificateAuthority
):
    template_in = schemas.CertificateTemplateCreate(
        template_name="Test Template",
        certificate_authorities=[db_ca.ca_name],
    )
    _, created_template = await crud.create_certificate_template(db=db_session, certificate_template=template_in)

    response = await authenticated_client.get(f"/certificate_templates/{created_template.id}")

    assert response.status_code == 200
    assert response.json()["template_name"] == "Test Template"


@pytest.mark.asyncio
async def test_get_certificate_template_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/certificate_templates/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_update_certificate_template(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_ca: schemas.CertificateAuthority
):
    template_in = schemas.CertificateTemplateCreate(
        template_name="Test Template",
        certificate_authorities=[db_ca.ca_name],
    )
    _, created_template = await crud.create_certificate_template(db=db_session, certificate_template=template_in)

    update_data = {
        "template_name": "Updated Template",
    }
    response = await authenticated_client.put(f"/certificate_templates/{created_template.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["template_name"] == "Updated Template"


@pytest.mark.asyncio
async def test_get_certificate_templates_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/certificate_templates/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
