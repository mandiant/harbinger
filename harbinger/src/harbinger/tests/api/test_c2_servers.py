import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_c2_server_type(db_session: AsyncSession) -> schemas.C2ServerType:
    server_type_in = schemas.C2ServerTypeCreate(
        id=uuid.uuid4(),
        name="Test C2 Type",
    )
    _, server_type = await crud.create_c2_server_type(db=db_session, c2_server_type=server_type_in)
    return schemas.C2ServerType.model_validate(server_type)


@pytest.mark.asyncio
async def test_read_c2_servers(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_c2_server_type: schemas.C2ServerType
):
    server_in = schemas.C2ServerCreate(
        c2_server_type_id=db_c2_server_type.id,
        name="Test Server",
        url="http://localhost",
        username="test",
        password="password",
    )
    await crud.create_c2_server(db=db_session, c2_server=server_in)

    response = await authenticated_client.get("/c2_servers/")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["name"] == "Test Server"


@pytest.mark.asyncio
async def test_read_c2_servers_empty(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/c2_servers/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}


# @pytest.mark.asyncio
# async def test_create_c2_server(authenticated_client: httpx.AsyncClient, db_c2_server_type: schemas.C2ServerType):
#     server_data = {
#         "c2_server_type_id": str(db_c2_server_type.id),
#         "name": "New Test Server",
#         "url": "http://newhost",
#         "username": "newuser",
#         "password": "newpassword",
#         "arguments": [],
#     }
#     response = await authenticated_client.post("/c2_servers/", json=server_data)

#     assert response.status_code == 200
#     assert response.json()["name"] == "New Test Server"


@pytest.mark.asyncio
async def test_get_c2_server_statistics(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/c2_servers/statistics")

    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


# @pytest.mark.asyncio
# async def test_c2_server_command(authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_c2_server_type: schemas.C2ServerType):
#     server_in = schemas.C2ServerCreate(
#         c2_server_type_id=db_c2_server_type.id,
#         name="Test Server",
#         url="http://localhost",
#         username="test",
#         password="password",
#     )
#     server = await crud.create_c2_server(db=db_session, c2_server=server_in)

#     command_data = {
#         "command": "sync",
#     }
#     response = await authenticated_client.post(f"/c2_servers/{server.id}/command", json=command_data)

#     assert response.status_code == 200
