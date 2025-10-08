import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_host(db_session: AsyncSession) -> schemas.Host:
    _, host = await crud.get_or_create_host(db_session, "SAHOST")
    return schemas.Host.model_validate(host)


@pytest.mark.asyncio
async def test_list_situational_awareness(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_host: schemas.Host
):
    sa_in = schemas.SituationalAwarenessCreate(
        name="Test SA",
        category="Test Category",
        value_string="test value",
    )
    await crud.get_or_create_situational_awareness(db=db_session, sa=sa_in)

    response = await authenticated_client.get("/situational_awareness/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_create_situational_awareness(authenticated_client: httpx.AsyncClient, db_host: schemas.Host):
    sa_data = {
        "name": "New SA",
        "category": "New Category",
        "value_string": "new value",
    }
    response = await authenticated_client.post("/situational_awareness/", json=sa_data)

    assert response.status_code == 200
    assert response.json()["name"] == "New SA"


@pytest.mark.asyncio
async def test_update_situational_awareness(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_host: schemas.Host
):
    sa_in = schemas.SituationalAwarenessCreate(
        name="Test SA",
        category="Test Category",
        value_string="test value",
    )
    _, created_sa = await crud.get_or_create_situational_awareness(db=db_session, sa=sa_in)

    update_data = {
        "name": "Updated SA",
        "category": "Updated Category",
        "value_string": "updated value",
    }
    response = await authenticated_client.put(f"/situational_awareness/{created_sa.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["name"] == "Updated SA"


@pytest.mark.asyncio
async def test_delete_situational_awareness(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_host: schemas.Host
):
    sa_in = schemas.SituationalAwarenessCreate(
        name="To Be Deleted",
        category="Test Category",
        value_string="delete me",
    )
    _, created_sa = await crud.get_or_create_situational_awareness(db=db_session, sa=sa_in)

    response = await authenticated_client.delete(f"/situational_awareness/{created_sa.id}")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_situational_awareness_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/situational_awareness/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
