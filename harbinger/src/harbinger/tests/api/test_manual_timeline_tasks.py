import httpx
import pytest
from harbinger import crud, schemas
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_create_manual_timeline_task(authenticated_client: httpx.AsyncClient):
    task_data = {
        "command_name": "Test Task",
        "description": "A test task",
        "time_started": "2025-01-01T12:00:00",
        "time_completed": "2025-01-01T13:00:00",
    }
    response = await authenticated_client.post("/manual_timeline_tasks/", json=task_data)

    assert response.status_code == 200
    assert response.json()["command_name"] == "Test Task"


@pytest.mark.asyncio
async def test_update_manual_timeline_task(authenticated_client: httpx.AsyncClient, db_session: AsyncSession):
    task_in = schemas.ManualTimelineTaskCreate(
        command_name="Test Task",
        output="A test task",
        time_started="2025-01-01T12:00:00",
        time_completed="2025-01-01T13:00:00",
    )
    created_task = await crud.create_manual_timeline_task(db=db_session, manual_timeline_tasks=task_in)

    update_data = {
        "command_name": "Updated Task",
        "output": "An updated task",
        "time_started": "2025-01-01T14:00:00",
        "time_completed": "2025-01-01T15:00:00",
    }
    response = await authenticated_client.put(f"/manual_timeline_tasks/{created_task.id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["command_name"] == "Updated Task"
