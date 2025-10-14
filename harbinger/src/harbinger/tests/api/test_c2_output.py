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
        hostname="http://localhost",
        type="test",
    )
    server = await crud.create_c2_server(db=db_session, c2_server=server_in)
    return schemas.C2Server.model_validate(server)


@pytest.fixture
async def db_c2_implant(db_session: AsyncSession, db_c2_server: schemas.C2Server) -> schemas.C2Implant:
    implant_in = schemas.C2ImplantCreate(
        internal_id=str(uuid.uuid4()),
        c2_server_id=db_c2_server.id,
        hostname="test-host",
        ip="127.0.0.1",
        username="test-user",
        architecture="x64",
        os="Windows",
    )
    _, implant = await crud.create_or_update_c2_implant(db=db_session, implant=implant_in)
    return schemas.C2Implant.model_validate(implant)


@pytest.fixture
async def db_c2_task(
    db_session: AsyncSession, db_c2_implant: schemas.C2Implant, db_c2_server: schemas.C2Server
) -> schemas.C2Task:
    task_in = schemas.C2TaskCreate(
        internal_implant_id=db_c2_implant.internal_id,
        c2_implant_id=db_c2_implant.id,
        c2_server_id=db_c2_server.id,
        command_name="whoami",
    )
    _, task = await crud.create_or_update_c2_task(db=db_session, task=task_in)
    return schemas.C2Task.model_validate(task)


@pytest.mark.asyncio
async def test_read_c2_output(
    authenticated_client: httpx.AsyncClient,
    db_session: AsyncSession,
    db_c2_task: schemas.C2Task,
    db_c2_server: schemas.C2Server,
):
    output_in = schemas.C2OutputCreate(
        c2_task_id=db_c2_task.id,
        response_text="test-output",
        c2_server_id=db_c2_server.id,
        internal_task_id="1",
    )
    await crud.create_c2_task_output(db=db_session, c2_output=output_in)
    task_id = db_c2_task.id

    response = await authenticated_client.get(f"/c2_output/?c2_task_id={task_id}")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["response_text"] == "test-output"


@pytest.mark.asyncio
async def test_read_c2_output_empty(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/c2_output/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}


@pytest.mark.asyncio
async def test_get_c2_output(
    authenticated_client: httpx.AsyncClient,
    db_session: AsyncSession,
    db_c2_task: schemas.C2Task,
    db_c2_server: schemas.C2Server,
):
    output_in = schemas.C2OutputCreate(
        c2_task_id=db_c2_task.id,
        response_text="test-output",
        c2_server_id=db_c2_server.id,
        internal_task_id="1",
    )
    _, created_output = await crud.create_c2_task_output(db=db_session, c2_output=output_in)
    output_id = created_output.id

    response = await authenticated_client.get(f"/c2_output/{output_id}")

    assert response.status_code == 200
    assert response.json()["response_text"] == "test-output"


@pytest.mark.asyncio
async def test_get_c2_output_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/c2_output/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_export_c2_output(
    authenticated_client: httpx.AsyncClient,
    db_session: AsyncSession,
    db_c2_task: schemas.C2Task,
    db_c2_server: schemas.C2Server,
):
    output_in = schemas.C2OutputCreate(
        c2_task_id=db_c2_task.id,
        response_text="test-output",
        c2_server_id=db_c2_server.id,
        internal_task_id="1",
    )
    await crud.create_c2_task_output(db=db_session, c2_output=output_in)
    task_id = db_c2_task.id

    response = await authenticated_client.get(f"/c2_output/export?c2_task_id={task_id}")

    assert response.status_code == 200
    assert response.text == "test-output"
    assert "attachment;filename=output.txt" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_get_c2_output_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/c2_output/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
