import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_get_label_categories(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    label_in = schemas.LabelCreate(
        name="Test Label",
        category="Test Category",
    )
    await crud.create_label(db=db_session, label=label_in)

    response = await authenticated_client.get("/label_categories/")

    assert response.status_code == 200
    assert "Test Category" in response.json()


@pytest.mark.asyncio
async def test_get_labels(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    label_in = schemas.LabelCreate(
        name="Test Label 2",
        category="Test Category 2",
    )
    await crud.create_label(db=db_session, label=label_in)

    response = await authenticated_client.get("/labels/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_labels_grouped(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    label_in = schemas.LabelCreate(
        name="Grouped Label",
        category="Grouped Category",
    )
    await crud.create_label(db=db_session, label=label_in)

    response = await authenticated_client.get("/labels/grouped")

    assert response.status_code == 200
    assert any(d["category"] == "Grouped Category" for d in response.json())


@pytest.mark.asyncio
async def test_create_label(authenticated_client: httpx.AsyncClient):
    label_data = {
        "name": "New Label",
        "category": "New Category",
    }
    response = await authenticated_client.post("/labels/", json=label_data)

    assert response.status_code == 200
    assert response.json()["name"] == "New Label"


@pytest.mark.asyncio
async def test_create_label_already_exists(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    label_in = schemas.LabelCreate(
        name="Existing Label",
        category="Existing Category",
    )
    await crud.create_label(db=db_session, label=label_in)

    label_data = {
        "name": "Existing Label",
        "category": "Existing Category",
    }
    response = await authenticated_client.post("/labels/", json=label_data)

    assert response.status_code == 422
