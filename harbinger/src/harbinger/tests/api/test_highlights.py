import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_list_highlights(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    highlight_in = schemas.HighlightCreate(
        hit="Test highlight",
    )
    await crud.create_highlight(db=db_session, highlight=highlight_in)

    response = await authenticated_client.get("/highlights/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_highlight(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    highlight_in = schemas.HighlightCreate(
        hit="Another test highlight",
    )
    created_highlight = await crud.create_highlight(db=db_session, highlight=highlight_in)

    response = await authenticated_client.get(f"/highlights/{created_highlight.id}")

    assert response.status_code == 200
    assert response.json()["hit"] == "Another test highlight"


@pytest.mark.asyncio
async def test_get_highlight_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/highlights/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_get_highlights_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/highlights/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
