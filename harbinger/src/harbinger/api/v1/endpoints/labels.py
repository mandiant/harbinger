import sqlalchemy.exc
from fastapi import APIRouter, Depends, Response, status
from fastapi_pagination import Page
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.config.dependencies import current_active_user

router = APIRouter()


@router.get("/", response_model=Page[schemas.Label], tags=["labels", "crud"])
async def get_labels(
    db: AsyncSession = Depends(get_db), user: models.User = Depends(current_active_user)
):
    return await crud.get_labels_paged(db)


@router.get("/grouped", response_model=list[schemas.LabelView], tags=["labels", "crud"])
async def get_labels_grouped(
    db: AsyncSession = Depends(get_db), user: models.User = Depends(current_active_user)
):
    return await crud.get_labels_grouped(db)


@router.post("/", response_model=schemas.Label, tags=["labels", "crud"])
async def create_label(
    label: schemas.LabelCreate,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    try:
        return await crud.create_label(db=db, label=label)
    except sqlalchemy.exc.IntegrityError:
        return Response(
            "Label already exists", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
