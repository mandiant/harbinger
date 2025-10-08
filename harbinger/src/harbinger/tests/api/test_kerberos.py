import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_kerberos_ticket(db_session: AsyncSession) -> schemas.Kerberos:
    ticket_in = schemas.KerberosCreate(
        client="test-client",
        server="test-server",
    )
    _, ticket = await crud.get_or_create_kerberos(db=db_session, kerberos=ticket_in)
    return schemas.Kerberos.model_validate(ticket)


@pytest.mark.asyncio
async def test_read_kerberos(authenticated_client: httpx.AsyncClient, db_kerberos_ticket: schemas.Kerberos):
    response = await authenticated_client.get("/kerberos/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_kerberos(authenticated_client: httpx.AsyncClient, db_kerberos_ticket: schemas.Kerberos):
    response = await authenticated_client.get(f"/kerberos/{db_kerberos_ticket.id}")

    assert response.status_code == 200
    assert response.json()["client"] == "test-client"


@pytest.mark.asyncio
async def test_get_kerberos_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/kerberos/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None
