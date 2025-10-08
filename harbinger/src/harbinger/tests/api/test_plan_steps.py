import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_plan(db_session: AsyncSession) -> schemas.Plan:
    plan_in = schemas.PlanCreate(name="Test Plan")
    _, plan = await crud.create_plan(db=db_session, plan=plan_in)
    return schemas.Plan.model_validate(plan)


@pytest.mark.asyncio
async def test_list_plan_steps(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_plan: schemas.Plan
):
    step_in = schemas.PlanStepCreate(
        plan_id=db_plan.id,
        description="Test Step",
    )
    await crud.create_plan_step(db=db_session, plan_step=step_in)

    response = await authenticated_client.get(f"/plan_steps/?plan_id={db_plan.id}")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_plan_step(authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_plan: schemas.Plan):
    step_in = schemas.PlanStepCreate(
        plan_id=db_plan.id,
        description="Test Step",
    )
    _, created_step = await crud.create_plan_step(db=db_session, plan_step=step_in)

    response = await authenticated_client.get(f"/plan_steps/{created_step.id}")

    assert response.status_code == 200
    assert response.json()["description"] == "Test Step"


@pytest.mark.asyncio
async def test_create_plan_step(authenticated_client: httpx.AsyncClient, db_plan: schemas.Plan):
    step_data = {
        "plan_id": str(db_plan.id),
        "description": "New Step",
    }
    response = await authenticated_client.post("/plan_steps/", json=step_data)

    assert response.status_code == 200
    assert response.json()["description"] == "New Step"


@pytest.mark.asyncio
async def test_update_plan_step(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_plan: schemas.Plan
):
    step_in = schemas.PlanStepCreate(
        plan_id=db_plan.id,
        description="Test Step",
    )
    _, created_step = await crud.create_plan_step(db=db_session, plan_step=step_in)

    update_data = {
        "description": "Updated Step",
    }
    response = await authenticated_client.put(f"/plan_steps/{created_step.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["description"] == "Updated Step"


@pytest.mark.asyncio
async def test_get_plan_steps_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/plan_steps/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
