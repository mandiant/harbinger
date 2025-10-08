import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_list_plans(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    plan_in = schemas.PlanCreate(name="Test Plan")
    await crud.create_plan(db=db_session, plan=plan_in)

    response = await authenticated_client.get("/plans/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_plan(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    plan_in = schemas.PlanCreate(name="Test Plan")
    _, created_plan = await crud.create_plan(db=db_session, plan=plan_in)

    response = await authenticated_client.get(f"/plans/{created_plan.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Test Plan"


# @pytest.mark.asyncio
# async def test_create_plan(authenticated_client: httpx.AsyncClient):
#     plan_data = {"name": "New Plan"}
#     response = await authenticated_client.post("/plans/", json=plan_data)

#     assert response.status_code == 200
#     assert response.json()["name"] == "New Plan"


@pytest.mark.asyncio
async def test_update_plan(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    plan_in = schemas.PlanCreate(name="Test Plan")
    _, created_plan = await crud.create_plan(db=db_session, plan=plan_in)

    update_data = {"name": "Updated Plan"}
    response = await authenticated_client.put(f"/plans/{created_plan.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Plan"


@pytest.mark.asyncio
async def test_get_plans_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/plans/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
