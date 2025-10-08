import uuid

import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def db_playbook_template(db_session: AsyncSession) -> schemas.PlaybookTemplate:
    template_in = schemas.PlaybookTemplateCreate(
        id=str(uuid.uuid4()),
        name="Test Playbook Template",
        yaml="""
name: Test Playbook
args: []
steps: ''
""",
    )
    template = await crud.create_playbook_template(db=db_session, playbook_template=template_in)
    return schemas.PlaybookTemplate.model_validate(template)


@pytest.mark.asyncio
async def test_playbook_templates(
    authenticated_client: httpx.AsyncClient, db_playbook_template: schemas.PlaybookTemplate
):
    response = await authenticated_client.get("/job_templates/playbooks/")

    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_get_playbook_template(
    authenticated_client: httpx.AsyncClient, db_playbook_template: schemas.PlaybookTemplate
):
    response = await authenticated_client.get(f"/job_templates/playbooks/{db_playbook_template.id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Test Playbook Template"


@pytest.mark.asyncio
async def test_job_templates(authenticated_client: httpx.AsyncClient):
    response = await authenticated_client.get("/job_templates/c2/")
    assert response.status_code == 200
    assert "templates" in response.json()

    response = await authenticated_client.get("/job_templates/proxy/")
    assert response.status_code == 200
    assert "templates" in response.json()


@pytest.mark.asyncio
async def test_chain_templates_schema(
    authenticated_client: httpx.AsyncClient, db_playbook_template: schemas.PlaybookTemplate
):
    response = await authenticated_client.get(f"/job_templates/playbooks/{db_playbook_template.id}/schema")
    assert response.status_code == 200
    assert "title" in response.json()


@pytest.mark.asyncio
async def test_create_chain_template(authenticated_client: httpx.AsyncClient):
    template_data = {
        "id": str(uuid.uuid4()),
        "name": "New Playbook Template",
        "yaml": """
name: New Playbook Template
args: []
steps: ''
        """,
    }
    response = await authenticated_client.post("/job_templates/playbooks/", json=template_data)
    assert response.status_code == 200
    assert response.json()["name"] == "New Playbook Template"
