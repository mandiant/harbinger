import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_host(db_session: AsyncSession) -> schemas.Host:
    _, host = await crud.get_or_create_host(db_session, "PROCHOST")
    return schemas.Host.model_validate(host)


@pytest.fixture
async def db_process(db_session: AsyncSession, db_host: schemas.Host) -> schemas.Process:
    process_in = schemas.ProcessCreate(
        host_id=db_host.id,
        process_id=1234,
        name="test.exe",
        number=1,
    )
    process = await crud.create_process(db=db_session, process=process_in)
    return schemas.Process.model_validate(process)


@pytest.mark.asyncio
async def test_get_processes(authenticated_client: httpx.AsyncClient, db_process: schemas.Process):
    response = await authenticated_client.get(f"/processes/?host_id={db_process.host_id}")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_process_numbers(authenticated_client: httpx.AsyncClient, db_process: schemas.Process):
    response = await authenticated_client.get(f"/processes/numbers/?host_id={db_process.host_id}")

    assert response.status_code == 200
    assert "items" in response.json()
    assert isinstance(response.json()["items"], list)
    assert response.json()["items"][0] == 1
