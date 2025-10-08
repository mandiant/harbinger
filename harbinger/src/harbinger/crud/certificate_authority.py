from collections.abc import Iterable

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import apaginate
from pydantic import UUID4
from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas

from ._common import create_filter_for_column
from .label import get_labels_for_q


async def create_certificate_authority_map(
    db: AsyncSession,
    certificate_authority_id: UUID4 | str,
    certificate_template_id: UUID4 | str,
) -> None:
    q = insert(models.CertificateAuthorityMap).values(
        certificate_authority_id=certificate_authority_id,
        certificate_template_id=certificate_template_id,
    )
    update_stmt = q.on_conflict_do_nothing("authority_template_id_uc")
    await db.execute(update_stmt)
    await db.commit()


async def get_certificate_authority(
    db: AsyncSession,
    id: UUID4,
) -> models.CertificateAuthority | None:
    return await db.get(models.CertificateAuthority, id)


async def create_certificate_authority(
    db: AsyncSession,
    certificate_authority: schemas.CertificateAuthorityCreate,
) -> tuple[bool, models.CertificateAuthority]:
    data = certificate_authority.model_dump()
    q = insert(models.CertificateAuthority).values(**data)
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update("ca_dns_name_uc", set_=data)
    res = await db.scalars(
        update_stmt.returning(models.CertificateAuthority),
        execution_options={"populate_existing": True},
    )
    result = res.unique().one()
    was_created = result.time_updated is None
    await db.commit()
    await db.refresh(result)
    return (was_created, result)


async def get_certificate_authorities(
    db: AsyncSession,
    filters: filters.CertificateAuthorityFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.CertificateAuthority]:
    q: Select = select(models.CertificateAuthority)
    q = q.outerjoin(models.CertificateAuthority.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.CertificateAuthority.id)
    q = q.offset(offset)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.unique().scalars().all()


async def get_certificate_authorities_paged(
    db: AsyncSession,
    filters: filters.CertificateAuthorityFilter,
) -> Page[models.CertificateAuthority]:
    q: Select = select(models.CertificateAuthority)
    q = q.outerjoin(models.CertificateAuthority.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.CertificateAuthority.id)
    return await apaginate(db, q)


async def get_certificate_authorities_filters(
    db: AsyncSession,
    filters: filters.CertificateAuthorityFilter,
):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.CertificateAuthority.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["ca_name", "dns_name"]:
        res = await create_filter_for_column(
            db,
            q,
            getattr(models.CertificateAuthority, field),
            field,
            field,
        )
        result.append(res)
    return result
