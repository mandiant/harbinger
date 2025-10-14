import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_suggestion(db_session: AsyncSession) -> schemas.Suggestion:
    suggestion_in = schemas.SuggestionCreate(
        name="Test Suggestion",
        reason="A test suggestion",
    )
    _, suggestion = await crud.create_suggestion(db=db_session, suggestion=suggestion_in)
    return schemas.Suggestion.model_validate(suggestion)


@pytest.mark.asyncio
async def test_list_suggestions(authenticated_client: httpx.AsyncClient, db_suggestion: schemas.Suggestion):
    response = await authenticated_client.get("/suggestions/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_suggestion(authenticated_client: httpx.AsyncClient, db_suggestion: schemas.Suggestion):
    response = await authenticated_client.get(f"/suggestions/{db_suggestion.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Test Suggestion"


@pytest.mark.asyncio
async def test_create_suggestion(authenticated_client: httpx.AsyncClient):
    suggestion_data = {
        "name": "New Suggestion",
        "reason": "A new suggestion",
    }
    response = await authenticated_client.post("/suggestions/", json=suggestion_data)

    assert response.status_code == 200
    assert response.json()["name"] == "New Suggestion"


@pytest.mark.asyncio
async def test_update_suggestion(authenticated_client: httpx.AsyncClient, db_suggestion: schemas.Suggestion):
    update_data = {
        "name": "Updated Suggestion",
        "reason": "An updated suggestion",
    }
    response = await authenticated_client.put(f"/suggestions/{db_suggestion.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Suggestion"


@pytest.mark.asyncio
async def test_get_suggestions_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/suggestions/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
