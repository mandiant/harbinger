import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_password(db_session: AsyncSession) -> schemas.Password:
    password = await crud.get_or_create_password(db=db_session, password="testpassword")
    return schemas.Password.model_validate(password)


@pytest.mark.asyncio
async def test_read_credentials(authenticated_client: httpx.AsyncClient, db_password: schemas.Password):
    credential_in = {
        "username": "testuser",
        "password_id": str(db_password.id),
    }
    post_response = await authenticated_client.post("/credentials/", json=credential_in)
    assert post_response.status_code == 200

    get_response = await authenticated_client.get("/credentials/")

    assert get_response.status_code == 200
    assert len(get_response.json()["items"]) == 1
    assert get_response.json()["items"][0]["username"] == "testuser"


@pytest.mark.asyncio
async def test_read_credentials_empty(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/credentials/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}


@pytest.mark.asyncio
async def test_read_credential(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_password: schemas.Password
):
    credential_in = schemas.CredentialCreate(
        username="testuser",
        password_id=db_password.id,
    )
    created_credential = await crud.create_credential(db=db_session, credential=credential_in)
    credential_id = created_credential.id
    await db_session.commit()

    response = await authenticated_client.get(f"/credentials/{credential_id}")

    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


@pytest.mark.asyncio
async def test_read_credential_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/credentials/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_create_credential(authenticated_client: httpx.AsyncClient, db_password: schemas.Password):
    credential_data = {
        "username": "newuser",
        "password_id": str(db_password.id),
    }
    response = await authenticated_client.post("/credentials/", json=credential_data)

    assert response.status_code == 200
    assert response.json()["username"] == "newuser"


@pytest.mark.asyncio
async def test_get_credentials_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/credentials/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
