import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_get_actions(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    action_id = uuid.uuid4()
    action_in = schemas.ActionCreate(
        id=action_id,
        name="Test Action",
        description="A test action.",
    )
    await crud.create_action(db=db_session, action=action_in)

    response = await authenticated_client.get("/actions/")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["name"] == "Test Action"


@pytest.mark.asyncio
async def test_get_action(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    action_id = uuid.uuid4()
    action_in = schemas.ActionCreate(
        id=action_id,
        name="Test Action",
        description="A test action.",
    )
    await crud.create_action(db=db_session, action=action_in)

    response = await authenticated_client.get(f"/actions/{action_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Test Action"


@pytest.mark.asyncio
async def test_get_actions_empty(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/actions/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}


@pytest.mark.asyncio
async def test_get_action_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_uuid = uuid.uuid4()
    response = await authenticated_client.get(f"/actions/{non_existent_uuid}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_get_actions_with_pagination(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    action1_id = uuid.uuid4()
    action1_in = schemas.ActionCreate(
        id=action1_id,
        name="Test Action 1",
        description="A test action.",
    )
    await crud.create_action(db=db_session, action=action1_in)

    action2_id = uuid.uuid4()
    action2_in = schemas.ActionCreate(
        id=action2_id,
        name="Test Action 2",
        description="Another test action.",
    )
    await crud.create_action(db=db_session, action=action2_in)

    response = await authenticated_client.get("/actions/?size=1")

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["total"] == 2
    assert len(response_json["items"]) == 1
    assert response_json["page"] == 1
    assert response_json["size"] == 1
    assert response_json["pages"] == 2

    response_page_2 = await authenticated_client.get("/actions/?size=1&page=2")
    assert response_page_2.status_code == 200
    response_json_2 = response_page_2.json()
    assert len(response_json_2["items"]) == 1


@pytest.mark.asyncio
async def test_get_actions_filtered_by_status(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    action1_id = uuid.uuid4()
    action1_in = schemas.ActionCreate(
        id=action1_id,
        name="Action running",
        description="A test action.",
        status="running",
    )
    await crud.create_action(db=db_session, action=action1_in)

    action2_id = uuid.uuid4()
    action2_in = schemas.ActionCreate(
        id=action2_id,
        name="Action pending",
        description="Another test action.",
        status="pending",
    )
    await crud.create_action(db=db_session, action=action2_in)

    response = await authenticated_client.get("/actions/?status=running")

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["total"] == 1
    assert len(response_json["items"]) == 1
    assert response_json["items"][0]["name"] == "Action running"
    assert response_json["items"][0]["status"] == "running"


async def test_get_actions_filtered_by_search(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    action1_id = uuid.uuid4()
    action1_in = schemas.ActionCreate(
        id=action1_id,
        name="Find This Action",
        description="A test action.",
    )
    await crud.create_action(db=db_session, action=action1_in)

    action2_id = uuid.uuid4()
    action2_in = schemas.ActionCreate(
        id=action2_id,
        name="Not This One",
        description="Another test action.",
    )
    await crud.create_action(db=db_session, action=action2_in)

    response = await authenticated_client.get("/actions/?search=Find This")

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["total"] == 1
    assert len(response_json["items"]) == 1
    assert response_json["items"][0]["name"] == "Find This Action"
