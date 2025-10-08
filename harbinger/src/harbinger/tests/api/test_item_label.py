import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_label(db_session: AsyncSession) -> schemas.Label:
    label_in = schemas.LabelCreate(
        name="Test Label",
        category="Test",
    )
    label = await crud.create_label(db=db_session, label=label_in)
    return schemas.Label.model_validate(label)


@pytest.fixture
async def db_host(db_session: AsyncSession) -> schemas.Host:
    _, host = await crud.get_or_create_host(db_session, "LABELHOST")
    return schemas.Host.model_validate(host)


@pytest.mark.asyncio
async def test_create_label_mapping(
    authenticated_client: httpx.AsyncClient, db_label: schemas.Label, db_host: schemas.Host
):
    mapping_data = {
        "label_id": str(db_label.id),
        "object_id": str(db_host.id),
    }
    response = await authenticated_client.post("/item_label/", json=mapping_data)

    assert response.status_code == 200
    assert response.json()["label_id"] == str(db_label.id)
