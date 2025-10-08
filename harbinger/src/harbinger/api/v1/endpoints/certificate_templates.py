from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination import Page
from harbinger import crud, filters, models, schemas
from harbinger.config.dependencies import current_active_user, get_db
from pydantic import UUID4
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get(
    "/",
    response_model=Page[schemas.CertificateTemplate],
    tags=["crud", "certificate_templates"],
)
async def get_certificate_templates(
    filters: filters.CertificateTemplateFilter = FilterDepends(
        filters.CertificateTemplateFilter,
    ),
    enroll_permissions: str = "",
    owner_permissions: str = "",
    writeowner_permissions: str = "",
    fullcontrol_permissions: str = "",
    writedacl_permissions: str = "",
    writeproperty_permissions: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_certificate_templates_paged(
        db,
        filters,
        enroll_permissions=enroll_permissions,
        owner_permissions=owner_permissions,
        writeowner_permissions=writeowner_permissions,
        fullcontrol_permissions=fullcontrol_permissions,
        writedacl_permissions=writedacl_permissions,
        writeproperty_permissions=writeproperty_permissions,
    )


@router.put(
    "/{id}",
    response_model=schemas.CertificateTemplate | None,
    tags=["crud", "certificate_templates"],
)
async def update_certificate_template(
    id: UUID4,
    certificate_template: schemas.CertificateTemplateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.update_certificate_template(
        db, certificate_template_id=id, certificate_template=certificate_template
    )


@router.get(
    "/filters",
    response_model=list[schemas.Filter],
    tags=["certificate_templates", "crud"],
)
async def certificate_templates_filters(
    filters: filters.CertificateTemplateFilter = FilterDepends(
        filters.CertificateTemplateFilter,
    ),
    enroll_permissions: str = "",
    owner_permissions: str = "",
    writeowner_permissions: str = "",
    fullcontrol_permissions: str = "",
    writedacl_permissions: str = "",
    writeproperty_permissions: str = "",
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_certificate_templates_filters(
        db,
        filters,
        enroll_permissions=enroll_permissions,
        owner_permissions=owner_permissions,
        writeowner_permissions=writeowner_permissions,
        fullcontrol_permissions=fullcontrol_permissions,
        writedacl_permissions=writedacl_permissions,
        writeproperty_permissions=writeproperty_permissions,
    )


@router.get(
    "/{id}",
    response_model=schemas.CertificateTemplate | None,
    tags=["crud", "certificate_templates"],
)
async def get_certificate_template(
    id: UUID4,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[models.User, Depends(current_active_user)],
):
    return await crud.get_certificate_template(db, id)
