import uuid

from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config import constants
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.connectors.workflows import C2ServerCommand
from harbinger.worker.client import get_client
from harbinger.worker.workflows import SyncAll

router = APIRouter()


@router.get("/", response_model=Page[schemas.C2Server], tags=["c2", "implants", "crud"])
async def read_c2_servers(
    db: AsyncSession = Depends(get_db), user: models.User = Depends(current_active_user)
):
    return await crud.get_c2_servers_paged(db)


@router.post(
    "/", response_model=schemas.C2Server | None, tags=["c2", "implants", "crud"]
)
async def create_c2_server(
    server: schemas.C2ServerCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    server = await crud.create_c2_server(db, c2_server=server)
    if not server:
        return None
    command = schemas.C2ServerCommand(
        command=schemas.Command.create, id=server.id, c2_server=server
    )
    client = await get_client()
    await client.start_workflow(
        C2ServerCommand.run,
        command,
        task_queue="c2_server_commands",
        id=str(uuid.uuid4()),
    )
    return server


@router.get(
    "/statistics",
    response_model=schemas.StatisticsItems,
    tags=["crud", "statistics"],
)
async def get_c2_server_statistics(user: models.User = Depends(current_active_user)):
    return await crud.get_c2_server_statistics()


@router.post("/{server_id}/command", tags=["c2", "implants", "crud"])
async def c2_server_command(
    server_id: UUID4,
    data: schemas.C2ServerCommand,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    server = await crud.get_c2_server(db, c2_server_id=server_id)
    client = await get_client()
    if data.command == "sync":
        await client.start_workflow(
            SyncAll.run,
            str(server_id),
            task_queue=constants.WORKER_TASK_QUEUE,
            id=str(uuid.uuid4()),
        )
    else:
        data.c2_server = server
        data.id = server_id
        await client.start_workflow(
            C2ServerCommand.run,
            data,
            task_queue="c2_server_commands",
            id=str(uuid.uuid4()),
        )
    return ""
