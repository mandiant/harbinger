# import uuid

# import httpx
# import pytest
# from harbinger import crud, schemas
# from sqlalchemy.ext.asyncio import AsyncSession

# pytestmark = pytest.mark.asyncio


# @pytest.fixture
# async def db_playbook(db_session: AsyncSession) -> schemas.Playbook:
#     playbook_in = schemas.PlaybookCreate(playbook_name="Test Playbook for Steps")
#     playbook = await crud.create_chain(db=db_session, chain=playbook_in)
#     return schemas.Playbook.model_validate(playbook)


# @pytest.fixture
# async def db_step(db_session: AsyncSession, db_playbook: schemas.Playbook) -> schemas.PlaybookStep:
#     step_in = schemas.PlaybookStepCreate(
#         playbook_id=db_playbook.id,
#         label="Test Step",
#     )
#     step = await crud.add_step(db=db_session, step=step_in)
#     return schemas.PlaybookStep.model_validate(step)


# @pytest.mark.asyncio
# async def test_get_step_modifiers(authenticated_client: httpx.AsyncClient, db_session: AsyncSession, db_step: schemas.PlaybookStep):
#     modifier_in = schemas.PlaybookStepModifierCreate(
#         playbook_step_id=db_step.id,
#         regex=".*",
#     )
#     await crud.create_playbook_step_modifier(db=db_session, step=modifier_in)

#     response = await authenticated_client.get(f"/step_modifiers/?playbook_step_id={db_step.id}")

#     assert response.status_code == 200
#     assert len(response.json()["items"]) >= 1


# @pytest.mark.asyncio
# async def test_add_step_modifier(authenticated_client: httpx.AsyncClient, db_step: schemas.PlaybookStep):
#     modifier_data = {
#         "playbook_step_id": str(db_step.id),
#         "regex": ".*",
#     }
#     response = await authenticated_client.post("/step_modifiers/", json=modifier_data)

#     assert response.status_code == 200
#     assert response.json()["regex"] == ".*"


# @pytest.mark.asyncio
# async def test_get_steps(authenticated_client: httpx.AsyncClient, db_step: schemas.PlaybookStep):
#     response = await authenticated_client.get(f"/steps/?playbook_id={db_step.playbook_id}")

#     assert response.status_code == 200
#     assert len(response.json()["items"]) >= 1


# @pytest.mark.asyncio
# async def test_get_step(authenticated_client: httpx.AsyncClient, db_step: schemas.PlaybookStep):
#     response = await authenticated_client.get(f"/steps/{db_step.id}")

#     assert response.status_code == 200
#     assert response.json()["label"] == "Test Step"


# @pytest.mark.asyncio
# async def test_add_step(authenticated_client: httpx.AsyncClient, db_playbook: schemas.Playbook):
#     step_data = {
#         "playbook_id": str(db_playbook.id),
#         "label": "New Step",
#     }
#     response = await authenticated_client.post("/steps/", json=step_data)

#     assert response.status_code == 200
#     assert response.json()["label"] == "New Step"


# @pytest.mark.asyncio
# async def test_clone_step(authenticated_client: httpx.AsyncClient, db_step: schemas.PlaybookStep):
#     response = await authenticated_client.post(f"/steps/{db_step.id}/clone")

#     assert response.status_code == 200
#     assert response.json()["label"] != db_step.label  # Cloned step should have a new label
#     assert response.json()["id"] != str(db_step.id)


# @pytest.mark.asyncio
# async def test_update_step(authenticated_client: httpx.AsyncClient, db_step: schemas.PlaybookStep):
#     update_data = {
#         "playbook_id": str(db_step.playbook_id),
#         "label": "Updated Step",
#     }
#     response = await authenticated_client.put(f"/steps/{db_step.id}", json=update_data)

#     assert response.status_code == 200
#     assert response.json()["label"] == "Updated Step"
