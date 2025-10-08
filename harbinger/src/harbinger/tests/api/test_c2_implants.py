import uuid
from datetime import UTC, datetime

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
        c2_server_type="sliver",
    )
    server_db = await crud.create_c2_server(db=db_session, c2_server=server_in)
    return schemas.C2Server.model_validate(server_db)


@pytest.mark.asyncio
async def test_read_c2_implants(
    authenticated_client: httpx.AsyncClient,
    db_session: AsyncSession,
    db_c2_server: schemas.C2Server,
):
    implant_id = str(uuid.uuid4())
    implant_in = schemas.C2ImplantCreate(
        internal_id=implant_id,
        c2_server_id=db_c2_server.id,
        hostname="test-host",
        ip_address="127.0.0.1",
        username="test-user",
        architecture="x64",
        os="Windows",
        last_checkin=datetime.now(UTC),
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
    await crud.create_or_update_c2_implant(db=db_session, implant=implant_in)

    response = await authenticated_client.get("/c2_implants/")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["hostname"] == "test-host"


@pytest.mark.asyncio
async def test_read_c2_implants_empty(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/c2_implants/")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "size": 50, "pages": 0}


@pytest.mark.asyncio
async def test_read_c2_implant(
    authenticated_client: httpx.AsyncClient,
    db_session: AsyncSession,
    db_c2_server: schemas.C2Server,
):
    implant_id = str(uuid.uuid4())
    implant_in = schemas.C2ImplantCreate(
        internal_id=implant_id,
        c2_server_id=db_c2_server.id,
        hostname="test-host",
        ip_address="127.0.0.1",
        username="test-user",
        architecture="x64",
        os="Windows",
        last_checkin=datetime.now(UTC),
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
    _, db_implant = await crud.create_or_update_c2_implant(db=db_session, implant=implant_in)

    response = await authenticated_client.get(f"/c2_implants/{db_implant.id}")

    assert response.status_code == 200
    assert response.json()["hostname"] == "test-host"


@pytest.mark.asyncio
async def test_read_c2_implant_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = str(uuid.uuid4())
    response = await authenticated_client.get(f"/c2_implants/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_read_c2_implants_with_pagination(
    authenticated_client: httpx.AsyncClient,
    db_session: AsyncSession,
    db_c2_server: schemas.C2Server,
):
    implant1_id = str(uuid.uuid4())
    implant1_in = schemas.C2ImplantCreate(
        internal_id=implant1_id,
        c2_server_id=db_c2_server.id,
        hostname="test-host-1",
        ip_address="127.0.0.1",
        username="test-user",
        architecture="x64",
        os="Windows",
        last_checkin=datetime.now(UTC),
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
    await crud.create_or_update_c2_implant(db=db_session, implant=implant1_in)

    implant2_id = str(uuid.uuid4())
    implant2_in = schemas.C2ImplantCreate(
        internal_id=implant2_id,
        c2_server_id=db_c2_server.id,
        hostname="test-host-2",
        ip_address="127.0.0.2",
        username="test-user-2",
        architecture="x64",
        os="Linux",
        last_checkin=datetime.now(UTC),
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
    await crud.create_or_update_c2_implant(db=db_session, implant=implant2_in)

    response = await authenticated_client.get("/c2_implants/?size=1")

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["total"] == 2
    assert len(response_json["items"]) == 1
    assert response_json["page"] == 1
    assert response_json["size"] == 1
    assert response_json["pages"] == 2

    response_page_2 = await authenticated_client.get("/c2_implants/?size=1&page=2")
    assert response_page_2.status_code == 200
    response_json_2 = response_page_2.json()
    assert len(response_json_2["items"]) == 1


@pytest.mark.asyncio
async def test_get_c2_implant_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/c2_implants/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
