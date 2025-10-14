import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_socks_server(db_session: AsyncSession) -> schemas.SocksServer:
    server_in = schemas.SocksServerCreate(
        id=uuid.uuid4(),
        type="local",
        hostname="test",
        operating_system="windows",
    )
    server = await crud.create_socks_server(db=db_session, socks_server=server_in)
    return schemas.SocksServer.model_validate(server)


@pytest.fixture
async def db_proxy_job(db_session: AsyncSession, db_socks_server: schemas.SocksServer) -> schemas.ProxyJob:
    job_in = schemas.ProxyJobCreate(
        socks_server_id=db_socks_server.id,
        command="test command",
    )
    proxy_job = await crud.create_proxy_job(db=db_session, proxy_job=job_in)
    return schemas.ProxyJob.model_validate(proxy_job)


@pytest.mark.asyncio
async def test_read_proxy_job_output(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_proxy_job: schemas.ProxyJob
):
    output_in = schemas.ProxyJobOutputCreate(
        job_id=db_proxy_job.id,
        output="test output",
    )
    await crud.create_proxy_job_output(db=db_session, output=output_in)

    response = await authenticated_client.get(f"/proxy_job_output/?job_id={db_proxy_job.id}")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_read_proxy_jobs(authenticated_client: httpx.AsyncClient, db_proxy_job: schemas.ProxyJob):
    response = await authenticated_client.get("/proxy_jobs/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_proxy_job(authenticated_client: httpx.AsyncClient, db_proxy_job: schemas.ProxyJob):
    response = await authenticated_client.get(f"/proxy_jobs/{db_proxy_job.id}")

    assert response.status_code == 200
    assert response.json()["command"] == "test command"


@pytest.mark.asyncio
async def test_create_proxy_job(authenticated_client: httpx.AsyncClient, db_socks_server: schemas.SocksServer):
    job_data = {
        "socks_server_id": str(db_socks_server.id),
        "command": "new command",
    }
    response = await authenticated_client.post("/proxy_jobs/", json=job_data)

    assert response.status_code == 200
    assert response.json()["command"] == "new command"


@pytest.mark.asyncio
async def test_update_proxy_job(authenticated_client: httpx.AsyncClient, db_proxy_job: schemas.ProxyJob):
    update_data = {
        "socks_server_id": str(db_proxy_job.socks_server_id),
        "command": "updated command",
    }
    response = await authenticated_client.put(f"/proxy_jobs/{db_proxy_job.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["command"] == "updated command"


# @pytest.mark.asyncio
# async def test_start_proxy_job(authenticated_client: httpx.AsyncClient, db_proxy_job: schemas.ProxyJob):
#     response = await authenticated_client.post(f"/proxy_jobs/{db_proxy_job.id}/start")

#     assert response.status_code == 200


@pytest.mark.asyncio
async def test_clone_proxy_job(authenticated_client: httpx.AsyncClient, db_proxy_job: schemas.ProxyJob):
    response = await authenticated_client.post(f"/proxy_jobs/{db_proxy_job.id}/clone")

    assert response.status_code == 200
    assert response.json()["command"] == db_proxy_job.command
    assert response.json()["id"] != str(db_proxy_job.id)


@pytest.mark.asyncio
async def test_get_proxy_job_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/proxy_jobs/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
