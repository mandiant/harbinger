import httpx
import pytest
from harbinger import crud
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_read_passwords(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    await crud.get_or_create_password(db=db_session, password="testpassword")

    response = await authenticated_client.get("/passwords/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_create_password(authenticated_client: httpx.AsyncClient):
    password_data = {"password": "newpassword"}
    response = await authenticated_client.post("/passwords/", json=password_data)

    assert response.status_code == 200
    assert response.json()["password"] == "newpassword"
