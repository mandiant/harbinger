from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas

from ._common import create_filter_for_column
from .certificate_authority import (
    create_certificate_authority_map,
    get_certificate_authorities,
)
from .label import get_labels_for_q


async def _apply_permission_filter(
    q: Select,
    permission_type: str,
    permission_value: str,
) -> Select:
    """Applies a permission filter to the query using a table alias to prevent conflicts.

    Args:
    ----
        q: The current SQLAlchemy Select query.
        permission_type: The type of permission (e.g., "Enroll", "Owner").
        permission_value: The principal associated with the permission.

    Returns:
    -------
        The modified SQLAlchemy Select query with the permission filter applied.

    """
    if permission_value:
        permission_alias = aliased(models.CertificateTemplatePermission)
        q = q.join(
            permission_alias,
            permission_alias.certificate_template_id == models.CertificateTemplate.id,
        )
        q = q.where(permission_alias.permission == permission_type)
        q = q.where(permission_alias.principal == permission_value)
    return q


async def create_certificate_permission_filter(
    db: AsyncSession,
    q: Select,
    permission_type: str,
) -> schemas.Filter:
    """Creates a filter option list for a given permission type based on the main query's results."""
    template_ids_subquery = q.with_only_columns(models.CertificateTemplate.id).distinct().subquery()
    permissions_q = (
        select(
            func.count(models.CertificateTemplatePermission.principal).label("count"),
            models.CertificateTemplatePermission.principal,
        )
        .where(
            models.CertificateTemplatePermission.certificate_template_id.in_(
                select(template_ids_subquery),
            ),
        )
        .where(models.CertificateTemplatePermission.permission == permission_type)
        .group_by(models.CertificateTemplatePermission.principal)
    )
    options: list[schemas.FilterOption] = []
    res = await db.execute(permissions_q)
    for count, principal in res.all():
        if principal is not None:
            options.append(schemas.FilterOption(name=str(principal), count=count))
    return schemas.Filter(
        name=f"{permission_type.lower()}_permissions",
        icon="",
        type="options",
        options=options,
        query_name=f"{permission_type.lower()}_permissions",
    )


async def get_certificate_templates_paged(
    db: AsyncSession,
    filters: filters.CertificateTemplateFilter,
    enroll_permissions: str = "",
    owner_permissions: str = "",
    writeowner_permissions: str = "",
    fullcontrol_permissions: str = "",
    writedacl_permissions: str = "",
    writeproperty_permissions: str = "",
) -> Page[models.CertificateTemplate]:
    q: Select = select(models.CertificateTemplate)
    q = q.outerjoin(models.CertificateTemplate.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.CertificateTemplate.id)
    q = await _apply_permission_filter(q, "Enroll", enroll_permissions)
    q = await _apply_permission_filter(q, "Owner", owner_permissions)
    q = await _apply_permission_filter(q, "WriteOwner", writeowner_permissions)
    q = await _apply_permission_filter(q, "FullControl", fullcontrol_permissions)
    q = await _apply_permission_filter(q, "WriteDACL", writedacl_permissions)
    q = await _apply_permission_filter(q, "WriteProperty", writeproperty_permissions)
    return await paginate(db, q)


async def get_certificate_templates_filters(
    db: AsyncSession,
    filters: filters.CertificateTemplateFilter,
    enroll_permissions: str = "",
    owner_permissions: str = "",
    writeowner_permissions: str = "",
    fullcontrol_permissions: str = "",
    writedacl_permissions: str = "",
    writeproperty_permissions: str = "",
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.CertificateTemplate.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    q = await _apply_permission_filter(q, "Enroll", enroll_permissions)
    q = await _apply_permission_filter(q, "Owner", owner_permissions)
    q = await _apply_permission_filter(q, "WriteOwner", writeowner_permissions)
    q = await _apply_permission_filter(q, "FullControl", fullcontrol_permissions)
    q = await _apply_permission_filter(q, "WriteDACL", writedacl_permissions)
    q = await _apply_permission_filter(q, "WriteProperty", writeproperty_permissions)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in [
        "enabled",
        "client_authentication",
        "enrollee_supplies_subject",
        "authorized_signatures_required",
        "requires_manager_approval",
    ]:
        res = await create_filter_for_column(
            db,
            q,
            getattr(models.CertificateTemplate, field),
            field,
            field,
        )
        result.append(res)
    permissions = [
        "Owner",
        "WriteOwner",
        "FullControl",
        "WriteDacl",
        "Enroll",
        "WriteProperty",
    ]
    for permission_type in permissions:
        permission_filter = await create_certificate_permission_filter(
            db,
            q,
            permission_type,
        )
        result.append(permission_filter)
    return result


async def get_certificate_template(
    db: AsyncSession,
    id: UUID4,
) -> models.CertificateTemplate | None:
    return await db.get(models.CertificateTemplate, id)


async def create_certificate_template(
    db: AsyncSession,
    certificate_template: schemas.CertificateTemplateCreate,
) -> tuple[bool, models.CertificateTemplate]:
    data = certificate_template.model_dump()
    authorities = data.pop("certificate_authorities")
    template_db = models.CertificateTemplate(**data)
    db.add(template_db)
    await db.commit()
    await db.refresh(template_db)
    for authority in authorities or []:
        auth_db = list(
            await get_certificate_authorities(
                db,
                filters.CertificateAuthorityFilter(ca_name=authority),
                0,
                1,
            ),
        )
        if auth_db:
            await create_certificate_authority_map(db, auth_db[0].id, template_db.id)
    return (True, template_db)


async def create_certificate_template_permissions(
    db: AsyncSession,
    certificate_template_permissions: schemas.CertificateTemplatePermissionCreate,
) -> tuple[bool, models.CertificateTemplatePermission]:
    data = certificate_template_permissions.model_dump()
    q = insert(models.CertificateTemplatePermission).values(**data)
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update(
        "certificate_template_permissions_uc",
        set_=data,
    )
    result = await db.scalars(
        update_stmt.returning(models.CertificateTemplatePermission),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    return (result.time_updated is None, result)
