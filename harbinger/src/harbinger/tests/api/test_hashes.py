import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_get_hashes(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    hash_in = schemas.HashCreate(
        hash="12345",
        type="ntlm",
    )
    await crud.create_hash(db=db_session, hash=hash_in)

    response = await authenticated_client.get("/hashes/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_hash(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    hash_in = schemas.HashCreate(
        hash="abcdef",
        type="ntlm",
    )
    _, created_hash = await crud.create_hash(db=db_session, hash=hash_in)

    response = await authenticated_client.get(f"/hashes/{created_hash.id}")

    assert response.status_code == 200
    assert response.json()["hash"] == "abcdef"


@pytest.mark.asyncio
async def test_create_hash(authenticated_client: httpx.AsyncClient):
    hash_data = {
        "hash": "fedcba",
        "type": "ntlm",
    }
    response = await authenticated_client.post("/hashes/", json=hash_data)

    assert response.status_code == 201
    assert response.json()["hash"] == "fedcba"


@pytest.mark.asyncio
async def test_update_hash(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    hash_in = schemas.HashCreate(
        hash="112233",
        type="ntlm",
    )
    _, created_hash = await crud.create_hash(db=db_session, hash=hash_in)

    update_data = {
        "hash": "332211",
        "type": "lm",
    }
    response = await authenticated_client.put(f"/hashes/{created_hash.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["hash"] == "332211"
    assert response.json()["type"] == "lm"


@pytest.mark.asyncio
async def test_delete_hash(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    hash_in = schemas.HashCreate(
        hash="tobedeleted",
        type="ntlm",
    )
    _, created_hash = await crud.create_hash(db=db_session, hash=hash_in)

    response = await authenticated_client.delete(f"/hashes/{created_hash.id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_export_hashes(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    hash_in = schemas.HashCreate(
        hash="exportme",
        type="ntlm",
    )
    await crud.create_hash(db=db_session, hash=hash_in)

    response = await authenticated_client.get("/hashes/export")

    assert response.status_code == 200
    assert "application/zip" in response.headers["content-type"]
