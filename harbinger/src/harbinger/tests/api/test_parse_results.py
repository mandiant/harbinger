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
        filename="parsable.txt",
        path="/tmp/parsable.txt",
        bucket="test-bucket",
        filetype=schemas.FileType.text,
    )
    return schemas.File.model_validate(file)


@pytest.fixture
async def db_parse_result(db_session: AsyncSession, db_file: schemas.File) -> schemas.ParseResult:
    result_in = schemas.ParseResultCreate(
        file_id=db_file.id,
        parser="Test Parser",
    )
    return await crud.create_parse_result(db=db_session, result=result_in)


@pytest.mark.asyncio
async def test_read_parse_results(authenticated_client: httpx.AsyncClient, db_parse_result: schemas.ParseResult):
    response = await authenticated_client.get(f"/parse_results/?file_id={db_parse_result.file_id}")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_parse_result(authenticated_client: httpx.AsyncClient, db_parse_result: schemas.ParseResult):
    response = await authenticated_client.get(f"/parse_results/{db_parse_result.id}")

    assert response.status_code == 200
    assert response.json()["parser"] == "Test Parser"


@pytest.mark.asyncio
async def test_get_parse_result_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/parse_results/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None
