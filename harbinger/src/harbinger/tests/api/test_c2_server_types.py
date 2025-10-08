import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_list_c2_server_types(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    server_type_in = schemas.C2ServerTypeCreate(
        name="Test C2 Type",
    )
    await crud.create_c2_server_type(db=db_session, c2_server_type=server_type_in)

    response = await authenticated_client.get("/c2_server_types/")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["name"] == "Test C2 Type"


@pytest.mark.asyncio
async def test_list_c2_server_types_empty(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/c2_server_types/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}


@pytest.mark.asyncio
async def test_list_c2_server_types_with_pagination(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    server_type1_in = schemas.C2ServerTypeCreate(
        name="Test C2 Type 1",
    )
    await crud.create_c2_server_type(db=db_session, c2_server_type=server_type1_in)

    server_type2_in = schemas.C2ServerTypeCreate(
        name="Test C2 Type 2",
    )
    await crud.create_c2_server_type(db=db_session, c2_server_type=server_type2_in)

    response = await authenticated_client.get("/c2_server_types/?size=1")

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["total"] == 2
    assert len(response_json["items"]) == 1
    assert response_json["page"] == 1
    assert response_json["size"] == 1
    assert response_json["pages"] == 2

    response_page_2 = await authenticated_client.get("/c2_server_types/?size=1&page=2")
    assert response_page_2.status_code == 200
    response_json_2 = response_page_2.json()
    assert len(response_json_2["items"]) == 1
