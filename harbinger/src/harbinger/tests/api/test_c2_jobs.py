import json
import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_c2_server(db_session: AsyncSession) -> schemas.C2Server:
    server_in = schemas.C2ServerCreate(
        name="Test Server",
        url="http://localhost",
        username="test",
        password="password",
        c2_server_type="test",
    )
    server = await crud.create_c2_server(db=db_session, c2_server=server_in)
    return schemas.C2Server.model_validate(server)


@pytest.fixture
async def db_c2_implant(db_session: AsyncSession, db_c2_server: schemas.C2Server) -> schemas.C2Implant:
    implant_id = str(uuid.uuid4())
    implant_in = schemas.C2ImplantCreate(
        internal_id=implant_id,
        c2_server_id=db_c2_server.id,
        hostname="test-host",
        ip_address="127.0.0.1",
        username="test-user",
        architecture="x64",
        os="Windows",
        c2_type="sliver",
        payload_type="http",
        name="test-implant",
        description="test-implant",
        sleep=60,
        jitter=10,
        external_ip="1.1.1.1",
        domain="test.local",
        process="test.exe",
        pid=1234,
        raw_json={},
    )
    _, implant = await crud.create_or_update_c2_implant(db=db_session, implant=implant_in)
    return schemas.C2Implant.model_validate(implant)


@pytest.mark.asyncio
async def test_read_c2_jobs(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_c2_implant: schemas.C2Implant
):
    job_in = schemas.C2JobCreate(
        c2_implant_id=db_c2_implant.id,
        command="whoami",
        arguments=json.dumps({}),
        c2_type="sliver",
    )
    await crud.create_c2_job(db=db_session, job=job_in)

    response = await authenticated_client.get("/c2_jobs/")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["command"] == "whoami"


@pytest.mark.asyncio
async def test_read_c2_jobs_empty(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/c2_jobs/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}


@pytest.mark.asyncio
async def test_get_c2_job(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_c2_implant: schemas.C2Implant
):
    job_in = schemas.C2JobCreate(
        c2_implant_id=db_c2_implant.id,
        command="whoami",
        arguments=json.dumps({}),
        c2_type="sliver",
    )
    db_job = await crud.create_c2_job(db=db_session, job=job_in)
    job_id = db_job.id

    response = await authenticated_client.get(f"/c2_jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["command"] == "whoami"


@pytest.mark.asyncio
async def test_get_c2_job_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = str(uuid.uuid4())
    response = await authenticated_client.get(f"/c2_jobs/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_create_c2_job(authenticated_client: httpx.AsyncClient, db_c2_implant: schemas.C2Implant):
    job_data = {
        "c2_implant_id": str(db_c2_implant.id),
        "command": "pwd",
        "arguments": json.dumps({}),
        "c2_type": "sliver",
    }
    response = await authenticated_client.post("/c2_jobs/", json=job_data)

    assert response.status_code == 200
    assert response.json()["command"] == "pwd"


@pytest.mark.asyncio
async def test_update_c2_job(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_c2_implant: schemas.C2Implant
):
    job_in = schemas.C2JobCreate(
        c2_implant_id=db_c2_implant.id,
        command="whoami",
        arguments=json.dumps({}),
        c2_type="sliver",
    )
    db_job = await crud.create_c2_job(db=db_session, job=job_in)
    job_id = db_job.id

    update_data = {
        "c2_implant_id": str(db_c2_implant.id),
        "command": "hostname",
        "arguments": json.dumps({}),
        "c2_type": "sliver",
    }
    response = await authenticated_client.put(f"/c2_jobs/{job_id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["command"] == "hostname"


# @pytest.mark.asyncio
# async def test_start_c2_job(authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_c2_implant: schemas.C2Implant):
#     job_in = schemas.C2JobCreate(
#         c2_implant_id=db_c2_implant.id,
#         command="whoami",
#         arguments=json.dumps({}),
#         status=schemas.Status.created,
#     )
#     db_job = await crud.create_c2_job(db=db_session, job=job_in)

#     response = await authenticated_client.post(f"/c2_jobs/{db_job.id}/start")

#     assert response.status_code == 200


@pytest.mark.asyncio
async def test_clone_c2_job(
    authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_c2_implant: schemas.C2Implant
):
    job_in = schemas.C2JobCreate(
        c2_implant_id=db_c2_implant.id,
        command="whoami",
        arguments=json.dumps({}),
        c2_type="sliver",
    )
    db_job = await crud.create_c2_job(db=db_session, job=job_in)
    job_id = db_job.id

    response = await authenticated_client.post(f"/c2_jobs/{job_id}/clone")

    assert response.status_code == 200
    assert response.json()["command"] == "whoami"
    assert response.json()["id"] != str(job_id)


@pytest.mark.asyncio
async def test_get_c2_jobs_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/c2_jobs/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
