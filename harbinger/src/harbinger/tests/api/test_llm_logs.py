import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_plan(db_session: AsyncSession) -> schemas.Plan:
    plan_in = schemas.PlanCreate(
        name="Test Plan",
    )
    _, plan = await crud.create_plan(db=db_session, plan=plan_in)
    return schemas.Plan.model_validate(plan)


@pytest.mark.asyncio
async def test_list_llm_logs(authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_plan: schemas.Plan):
    log_in = schemas.LlmLogCreate(
        plan_id=db_plan.id,
        prompt="Test prompt",
        response="Test response",
    )
    await crud.create_llm_log(db=db_session, llm_log=log_in)

    response = await authenticated_client.get("/llm_logs/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_llm_log(authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_plan: schemas.Plan):
    log_in = schemas.LlmLogCreate(
        plan_id=db_plan.id,
        log_type="REASONING",
        content={"key": "value"},
    )
    created_log = await crud.create_llm_log(db=db_session, llm_log=log_in)

    response = await authenticated_client.get(f"/llm_logs/{created_log.id}")

    assert response.status_code == 200
    assert response.json()["log_type"] == "REASONING"


@pytest.mark.asyncio
async def test_get_llm_logs_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/llm_logs/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
