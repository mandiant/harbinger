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
async def test_list_c2_server_arguments(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_c2_server_type: schemas.C2ServerType
):
    args_in = schemas.C2ServerArgumentsCreate(
        c2_server_type_id=db_c2_server_type.id,
        name="Test Argument",
        value="test_value",
    )
    await crud.create_c2_server_argument(db=db_session, c2_server_argument=args_in)

    response = await authenticated_client.get(f"/c2_server_arguments/?c2_server_type={db_c2_server_type.id}")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["name"] == "Test Argument"
