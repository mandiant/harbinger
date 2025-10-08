import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_playbook(db_session: AsyncSession) -> schemas.Playbook:
    playbook_in = schemas.PlaybookCreate(playbook_name="Test Playbook")
    playbook = await crud.create_chain(db=db_session, chain=playbook_in)
    return schemas.Playbook.model_validate(playbook)


@pytest.mark.asyncio
async def test_list_playbooks(authenticated_client: httpx.AsyncClient, db_playbook: schemas.Playbook):
    response = await authenticated_client.get("/playbooks/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_chain(authenticated_client: httpx.AsyncClient, db_playbook: schemas.Playbook):
    response = await authenticated_client.get(f"/playbooks/{db_playbook.id}")

    assert response.status_code == 200
    assert response.json()["playbook_name"] == "Test Playbook"


@pytest.mark.asyncio
async def test_create_chain(authenticated_client: httpx.AsyncClient):
    playbook_data = {"playbook_name": "New Playbook"}
    response = await authenticated_client.post("/playbooks/", json=playbook_data)

    assert response.status_code == 200
    assert response.json()["playbook_name"] == "New Playbook"


# @pytest.mark.asyncio
# async def test_update_chain(mock_publish, authenticated_client: httpx.AsyncClient, db_playbook: schemas.Playbook):
#     update_data = {"playbook_name": "Updated Playbook"}
#     response = await authenticated_client.put(f"/playbooks/{db_playbook.id}", json=update_data)

#     assert response.status_code == 200
#     assert response.json()["playbook_name"] == "Updated Playbook"


# @pytest.mark.asyncio
# async def test_start_chain(authenticated_client: httpx.AsyncClient, db_playbook: schemas.Playbook):
#     response = await authenticated_client.post(f"/playbooks/{db_playbook.id}/start")

#     assert response.status_code == 200


@pytest.mark.asyncio
async def test_clone_chain(authenticated_client: httpx.AsyncClient, db_playbook: schemas.Playbook):
    response = await authenticated_client.post(f"/playbooks/{db_playbook.id}/clone")

    assert response.status_code == 200
    assert response.json()["playbook_name"] == f"Clone of {db_playbook.playbook_name}"
    assert response.json()["id"] != str(db_playbook.id)


@pytest.mark.asyncio
async def test_get_playbook_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/playbooks/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
