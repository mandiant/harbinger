import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_list_objectives(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    objective_in = schemas.ObjectiveCreate(
        name="Test Objective",
        description="A test objective",
    )
    await crud.create_objective(db=db_session, objective=objective_in)

    response = await authenticated_client.get("/objectives/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_objective(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    objective_in = schemas.ObjectiveCreate(
        name="Test Objective",
        description="A test objective",
    )
    _, created_objective = await crud.create_objective(db=db_session, objective=objective_in)

    response = await authenticated_client.get(f"/objectives/{created_objective.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Test Objective"


@pytest.mark.asyncio
async def test_create_objective(authenticated_client: httpx.AsyncClient):
    objective_data = {
        "name": "New Objective",
        "description": "A new objective",
    }
    response = await authenticated_client.post("/objectives/", json=objective_data)

    assert response.status_code == 200
    assert response.json()["name"] == "New Objective"


@pytest.mark.asyncio
async def test_update_objective(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    objective_in = schemas.ObjectiveCreate(
        name="Test Objective",
        description="A test objective",
    )
    _, created_objective = await crud.create_objective(db=db_session, objective=objective_in)

    update_data = {
        "name": "Updated Objective",
        "description": "An updated objective",
    }
    response = await authenticated_client.put(f"/objectives/{created_objective.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Objective"


@pytest.mark.asyncio
async def test_get_objectives_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/objectives/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
