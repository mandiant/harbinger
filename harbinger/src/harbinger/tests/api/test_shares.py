import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_share(db_session: AsyncSession) -> schemas.Share:
    share_in = schemas.ShareCreate(
        name="Test Share",
        unc_path="/test/share",
    )
    share = await crud.get_or_create_share(db=db_session, share=share_in)
    return schemas.Share.model_validate(share)


@pytest.fixture
async def db_share_file(db_session: AsyncSession, db_share: schemas.Share) -> schemas.ShareFile:
    file_in = schemas.ShareFileCreate(
        share_id=db_share.id,
        name="testfile.txt",
        path="/test/share/testfile.txt",
    )
    share_file = await crud.create_share_file(db=db_session, share_file=file_in)
    return schemas.ShareFile.model_validate(share_file)


@pytest.mark.asyncio
async def test_list_share_files(authenticated_client: httpx.AsyncClient, db_share_file: schemas.ShareFile):
    response = await authenticated_client.get(f"/share_files/?share_id={db_share_file.share_id}")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_share_file(authenticated_client: httpx.AsyncClient, db_share_file: schemas.ShareFile):
    response = await authenticated_client.get(f"/share_files/{db_share_file.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "testfile.txt"


@pytest.mark.asyncio
async def test_get_share_files_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/share_files/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_shares(authenticated_client: httpx.AsyncClient, db_share: schemas.Share):
    response = await authenticated_client.get("/shares/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_share(authenticated_client: httpx.AsyncClient, db_share: schemas.Share):
    response = await authenticated_client.get(f"/shares/{db_share.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "TEST SHARE"


@pytest.mark.asyncio
async def test_create_share(authenticated_client: httpx.AsyncClient):
    share_data = {
        "name": "New Share",
        "unc_path": "/new/share",
    }
    response = await authenticated_client.post("/shares/", json=share_data)

    assert response.status_code == 200
    assert response.json()["name"] == "NEW SHARE"


@pytest.mark.asyncio
async def test_get_share_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/shares/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
