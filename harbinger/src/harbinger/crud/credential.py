import uuid
from collections.abc import Iterable

from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import UUID4
from sqlalchemy import Select, desc, exc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func

from harbinger import filters, models, schemas

from ._common import create_filter_for_column
from .label import get_labels_for_q


async def get_or_create_credential(
    db: AsyncSession,
    username: str,
    domain_id: str | uuid.UUID | None = None,
    password_id: str | uuid.UUID | None = None,
    kerberos_id: str | uuid.UUID | None = None,
) -> models.Credential:
    q = (
        select(models.Credential)
        .where(models.Credential.username.ilike(username))
        .where(models.Credential.domain_id == domain_id)
    )
    if password_id:
        q = q.where(models.Credential.password_id == password_id)
    if kerberos_id:
        q = q.where(models.Credential.kerberos_id == kerberos_id)
    res = await db.execute(q)
    try:
        credential = res.scalars().unique().one()
    except exc.NoResultFound:
        credential = models.Credential(
            username=username,
            domain_id=domain_id,
            password_id=password_id,
            kerberos_id=kerberos_id,
        )
        db.add(credential)
        await db.commit()
        await db.refresh(credential)
    return credential


async def get_credential(
    db: AsyncSession,
    credential_id: str | UUID4,
) -> models.Credential | None:
    return await db.get(models.Credential, credential_id)


async def get_credentials(
    db: AsyncSession,
    filters: filters.CredentialFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Credential]:
    q: Select = select(models.Credential)
    q = q.outerjoin(models.Credential.labels)
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def search_credentials(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Credential]:
    result = await db.execute(select(models.Credential).offset(offset).limit(limit))
    return result.scalars().unique().all()


async def get_credentials_paged(
    db: AsyncSession,
    filters: filters.CredentialFilter,
) -> Page[models.Credential]:
    q: Select = select(models.Credential)
    q = q.outerjoin(
        models.LabeledItem,
        onclause=models.Credential.id == models.LabeledItem.credential_id,
    )
    q = q.outerjoin(
        models.Label,
        onclause=models.LabeledItem.label_id == models.Label.id,
    )
    if filters.domain:
        q = q.select_from(models.Credential).join(
            models.Domain,
            onclause=models.Credential.domain_id == models.Domain.id,
        )
    q = filters.filter(q)
    q = filters.sort(q)
    q = q.group_by(models.Credential.id)
    return await paginate(db, q)


async def create_credential(
    db: AsyncSession,
    credential: schemas.CredentialCreate,
) -> models.Credential:
    credential_dict = credential.model_dump()
    credential_dict.pop("mark_owned", None)
    db_credential = models.Credential(**credential_dict)
    db.add(db_credential)
    await db.commit()
    await db.refresh(db_credential)
    return db_credential


async def get_credentials_filters(db: AsyncSession, filters: filters.CredentialFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Credential.id.distinct()).label("count_1"))
        .outerjoin(
            models.LabeledItem,
            onclause=models.Credential.id == models.LabeledItem.credential_id,
        )
        .outerjoin(
            models.Label,
            onclause=models.LabeledItem.label_id == models.Label.id,
        )
    )
    q = filters.filter(q)
    if filters.domain:
        q = q.select_from(models.Credential).join(
            models.Domain,
            onclause=models.Credential.domain_id == models.Domain.id,
        )
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    for field in ["username"]:
        res = await create_filter_for_column(
            db,
            q,
            getattr(models.Credential, field),
            field,
            field,
        )
        result.append(res)
    if not filters.domain:
        q = q.select_from(models.Credential).join(
            models.Domain,
            onclause=models.Credential.domain_id == models.Domain.id,
        )
    q = q.add_columns(models.Domain.long_name)
    q = q.group_by(models.Domain.long_name)
    q = q.order_by(desc("count_1"))
    options: list[schemas.FilterOption] = []
    res = await db.execute(q)
    for entry in res.unique().all():
        if entry[1] or not entry[1]:
            options.append(schemas.FilterOption(name=str(entry[1]), count=entry[0]))
    result.append(
        schemas.Filter(
            name="domain",
            icon="",
            type="options",
            options=options,
            query_name="domain__long_name",
        ),
    )
    return result
