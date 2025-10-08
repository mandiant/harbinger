import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_list_issues(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    issue_in = schemas.IssueCreate(
        name="Test Issue",
        description="A test issue",
    )
    await crud.create_issue(db=db_session, issue=issue_in)

    response = await authenticated_client.get("/issues/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_issue(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    issue_in = schemas.IssueCreate(
        name="Test Issue",
        description="A test issue",
    )
    _, created_issue = await crud.create_issue(db=db_session, issue=issue_in)

    response = await authenticated_client.get(f"/issues/{created_issue.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Test Issue"


@pytest.mark.asyncio
async def test_get_issue_not_found(authenticated_client: httpx.AsyncClient):
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/issues/{non_existent_id}")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_create_issue(authenticated_client: httpx.AsyncClient):
    issue_data = {
        "name": "New Issue",
        "description": "A new issue",
    }
    response = await authenticated_client.post("/issues/", json=issue_data)

    assert response.status_code == 200
    assert response.json()["name"] == "New Issue"


@pytest.mark.asyncio
async def test_update_issue(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    issue_in = schemas.IssueCreate(
        name="Test Issue",
        description="A test issue",
    )
    _, created_issue = await crud.create_issue(db=db_session, issue=issue_in)

    update_data = {
        "name": "Updated Issue",
        "description": "An updated issue",
    }
    response = await authenticated_client.put(f"/issues/{created_issue.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Issue"


@pytest.mark.asyncio
async def test_get_issue_filters(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/issues/filters")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
