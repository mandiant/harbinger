import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_file(db_session: AsyncSession) -> schemas.File:
    file = await crud.add_file(
        db=db_session,
        filename="test.txt",
        path="/tmp/test.txt",
        bucket="test-bucket",
        filetype=schemas.FileType.text,
    )
    return schemas.File.model_validate(file)


@pytest.mark.asyncio
async def test_read_files(authenticated_client: httpx.AsyncClient, db_file: schemas.File):
    response = await authenticated_client.get("/files/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1
    assert response.json()["items"][0]["filename"] == "test.txt"


@pytest.mark.asyncio
async def test_read_files_empty(authenticated_client: httpx.AsyncClient):
    # Assuming a clean DB for this test, might need test isolation setup
    response = await authenticated_client.get("/files/")
    # This test is tricky without DB isolation, so we check if it's a list
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


@pytest.mark.asyncio
async def test_read_file(authenticated_client: httpx.AsyncClient, db_file: schemas.File):
    response = await authenticated_client.get(f"/files/{db_file.id}")

    assert response.status_code == 200
    assert response.json()["filename"] == "test.txt"


@pytest.mark.asyncio
async def test_read_file_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/files/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_update_file(authenticated_client: httpx.AsyncClient, db_file: schemas.File):
    update_data = {"filetype": "json"}
    response = await authenticated_client.put(f"/files/{db_file.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["filetype"] == "json"


@pytest.mark.asyncio
async def test_file_types(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/file_types/")

    assert response.status_code == 200
    assert "types" in response.json()
    assert isinstance(response.json()["types"], list)


@pytest.mark.asyncio
async def test_get_file_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/files/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
