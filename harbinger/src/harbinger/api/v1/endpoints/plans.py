import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config import constants
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.enums import LlmStatus
from harbinger.worker.client import get_client
from harbinger.worker.supervisor_workflow import PlanSupervisorWorkflow
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession
from temporalio import exceptions
from temporalio.client import Client
from temporalio.service import RPCError, RPCStatusCode

router = APIRouter()


@router.get("/", response_model=Page[schemas.Plan], tags=["crud", "plans"])
async def list_plans(
    filters: filters.PlanFilter = FilterDepends(filters.PlanFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_plans_paged(db, filters)


@router.get("/filters", response_model=list[schemas.Filter], tags=["plans", "crud"])
async def plans_filters(
    filters: filters.PlanFilter = FilterDepends(filters.PlanFilter),
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_plans_filters(db, filters)


@router.get("/{id}", response_model=schemas.Plan | None, tags=["crud", "plans"])
async def get_plan(
    id: UUID4,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.get_plan(db, id)


@router.post("/", response_model=schemas.PlanCreated, tags=["plans"])
async def create_plan(
    plan: schemas.PlanCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    """Creates a new plan and starts the supervisor workflow for it."""
    _, new_plan = await crud.create_plan(db, plan)
    if not new_plan:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create the plan in the database.",
        )
    client = await get_client()
    try:
        await client.start_workflow(
            PlanSupervisorWorkflow.run,
            str(new_plan.id),
            id=f"supervisor-{new_plan.id}",
            task_queue=constants.WORKER_TASK_QUEUE,
        )
    except exceptions.WorkflowAlreadyStartedError:
        logging.warning(
            f"Workflow for plan {new_plan.id} already exists. This may be due to a race condition but is not a fatal error.",
        )
    except RPCError as e:
        logging.exception(f"Failed to start workflow for plan {new_plan.id}: {e}")
        await crud.update_plan(
            db,
            new_plan.id,
            schemas.PlanUpdate(llm_status=LlmStatus.INACTIVE),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plan created, but failed to start the supervisor workflow: {e.message}",
        )
    return new_plan


@router.put("/{id}", response_model=schemas.Plan | None, tags=["crud", "plans"])
async def update_plan(
    id: UUID4,
    plan_update: schemas.PlanUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    """Updates a plan's details. The supervisor will automatically start or stop
    if the 'status' field is changed to/from 'running'.
    """
    await crud.update_plan(db, id, plan_update)
    return await crud.get_plan(db, id)


@router.post("/{plan_id}/start_supervisor")
async def start_plan_supervisor(plan_id: str, client: Annotated[Client, Depends(get_client)]):
    """Starts the supervisor workflow for a given plan."""
    try:
        await client.start_workflow(
            PlanSupervisorWorkflow.run,
            plan_id,
            id=f"supervisor-{plan_id}",
            task_queue=constants.WORKER_TASK_QUEUE,
        )
        return {"status": f"Supervisor workflow started for plan {plan_id}"}
    except RPCError as e:
        if e.status == RPCStatusCode.ALREADY_EXISTS:
            return {"status": f"Supervisor for plan {plan_id} is already running."}
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plan_id}/stop_supervisor")
async def stop_plan_supervisor(
    plan_id: str,
    client: Annotated[Client, Depends(get_client)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Stops the supervisor workflow for a given plan."""
    try:
        handle = client.get_workflow_handle(f"supervisor-{plan_id}")
        await handle.signal(PlanSupervisorWorkflow.stop)
        return {"status": f"Stop signal sent to supervisor for plan {plan_id}"}
    except RPCError as e:
        if e.status == RPCStatusCode.NOT_FOUND:
            await crud.update_plan(
                db,
                plan_id,
                schemas.PlanUpdate(llm_status=LlmStatus.INACTIVE),
            )
            return {
                "status": f"Supervisor for plan {plan_id} was not running. Status ensured to be INACTIVE.",
            }
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plan_id}/force_update")
async def force_supervisor_update(plan_id: str, client: Annotated[Client, Depends(get_client)]):
    """Forces an immediate update cycle for a running supervisor."""
    try:
        handle = client.get_workflow_handle(f"supervisor-{plan_id}")
        await handle.signal(PlanSupervisorWorkflow.force_update)
        return {"status": f"Force update signal sent to supervisor for plan {plan_id}"}
    except RPCError as e:
        if e.status == RPCStatusCode.NOT_FOUND:
            raise HTTPException(
                status_code=404,
                detail=f"Supervisor for plan {plan_id} is not running.",
            )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
