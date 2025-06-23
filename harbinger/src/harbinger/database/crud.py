# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime, timedelta
import ntpath
from typing import Any, List, Optional, Tuple, Iterable, Union
import uuid
import jinja2
import yaml
import random
import string
import re


from harbinger.database.redis_pool import redis
import harbinger.proto.v1.messages_pb2 as messages_pb2
from harbinger.database.database import get_async_session
from fastapi import Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy import delete, desc, or_, select, update, and_, exc, Select
from sqlalchemy.orm import joinedload, InstrumentedAttribute, aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func
from sqlalchemy.dialects.postgresql import insert
from jinja2.sandbox import SandboxedEnvironment
from jinja2 import PackageLoader
from jinja2.ext import do
from sqlalchemy.exc import IntegrityError
import json
from pydantic import TypeAdapter, UUID4, ValidationError
from harbinger.database import filters
from harbinger.database.database import SessionLocal
from harbinger.database.cache import (
    redis_cache,
    redis_cache_invalidate,
    invalidate_cache_entry,
    redis_cache_fixed_key,
)

from . import models, schemas

import logging

CACHE_DECORATORS_AVAILABLE = True
DEFAULT_CACHE_TTL = 3600  # 1 hour

logger = logging.getLogger(__name__)


async def send_event(object_type: str, name: str, object_id: str | UUID4) -> None:
    event = messages_pb2.Event(
        event=object_type, name=name, id=str(object_id)
    ).SerializeToString()
    await redis.publish(
        schemas.Streams.events,
        event,
    )
    await redis.xadd(schemas.Streams.events, dict(message=event))  # type: ignore


@redis_cache(
    key_prefix="domain",
    session_factory=SessionLocal,
    schema=schemas.Domain,
    key_param_name="domain_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_domain(
    db: AsyncSession, domain_id: str | UUID4
) -> Optional[models.Domain]:
    return await db.get(models.Domain, domain_id)


async def get_or_create_domain(db: AsyncSession, name: str) -> models.Domain:
    name = name.upper()
    q = await db.execute(
        select(models.Domain).where(
            or_(
                models.Domain.long_name.ilike(name),
                models.Domain.short_name.ilike(name),
            )
        )
    )
    domain = q.scalars().first()
    if not domain:
        domain = models.Domain()
        q = insert(models.Domain)
        if "." in name:
            q = q.values(long_name=name)
            q = q.on_conflict_do_update(
                "domains_long_name_key",
                set_=dict(long_name=name),
            )
        else:
            q = q.values(short_name=name)
            q = q.on_conflict_do_update(
                "domains_short_name_key",
                set_=dict(short_name=name),
            )
        result = await db.scalars(
            q.returning(models.Domain), execution_options={"populate_existing": True}
        )
        await db.commit()
        return result.unique().one()
    return domain


async def get_or_create_password(
    db: AsyncSession,
    password: str | None = "",
    nt_hash: str | None = "",
    aes256_key: str | None = "",
    aes128_key: str | None = "",
) -> models.Password:
    q = select(models.Password)
    if password:
        q = q.where(models.Password.password == password)
    if nt_hash:
        nt_hash = nt_hash.lower()
        q = q.where(models.Password.nt == nt_hash)

    if aes128_key:
        aes128_key = aes128_key.lower()
        q = q.where(models.Password.aes128_key == aes128_key)

    if aes256_key:
        aes256_key = aes256_key.lower()
        q = q.where(models.Password.aes256_key == aes256_key)

    res = await db.execute(q)

    try:
        password_db = res.scalars().unique().one()
    except exc.NoResultFound:
        password_db = models.Password(
            password=password, nt=nt_hash, aes256_key=aes256_key, aes128_key=aes128_key
        )
        db.add(password_db)
        await db.commit()
        await db.refresh(password_db)
        await send_event(schemas.Event.password, schemas.EventType.new, password_db.id)
    return password_db


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
        await send_event(schemas.Event.credential, schemas.EventType.new, credential.id)
    return credential


async def get_or_create_kerberos(
    db: AsyncSession,
    kerberos: schemas.KerberosCreate,
) -> Tuple[bool, models.Kerberos]:
    q = (
        select(models.Kerberos)
        .where(models.Kerberos.client == kerberos.client)
        .where(models.Kerberos.server == kerberos.server)
        .where(models.Kerberos.key == kerberos.key)
        .where(models.Kerberos.auth == kerberos.auth)
        .where(models.Kerberos.start == kerberos.start)
        .where(models.Kerberos.end == kerberos.end)
        .where(models.Kerberos.renew == kerberos.renew)
        .where(models.Kerberos.keytype == kerberos.keytype)
    )

    res = await db.execute(q)
    try:
        kerberos = res.scalars().unique().one()
        return False, kerberos
    except exc.NoResultFound:
        kerberos = models.Kerberos(**kerberos.model_dump())
        db.add(kerberos)
        await db.commit()
        await db.refresh(kerberos)
        await send_event(schemas.Event.kerberos, schemas.EventType.new, kerberos.id)
        return True, kerberos


async def set_long_name(
    db: AsyncSession, domain_id: str | UUID4, long_name: str
) -> bool:
    try:
        q = (
            update(models.Domain)
            .where(models.Domain.id == domain_id)
            .values(long_name=long_name)
        )
        await db.execute(q)
        await db.commit()
        return True
    except IntegrityError:
        await db.rollback()
        return False


async def get_domains_paged(
    db: AsyncSession, filters: filters.DomainFilter
) -> Page[models.Domain]:
    q: Select = select(models.Domain)
    q = q.outerjoin(models.Domain.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.Domain.id)
    return await paginate(db, q)


async def get_domains(
    db: AsyncSession,
    filters: filters.DomainFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Domain]:
    q: Select = select(models.Domain)
    q = q.outerjoin(models.Domain.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_domains_filters(db: AsyncSession, filters: filters.DomainFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Domain.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


async def create_domain(
    db: AsyncSession, domain: schemas.DomainCreate
) -> models.Domain:
    db_domain = models.Domain(**domain.model_dump())
    db.add(db_domain)
    await db.commit()
    await db.refresh(db_domain)
    await send_event(schemas.Event.domain, schemas.EventType.new, db_domain.id)
    return db_domain


@redis_cache_invalidate(
    key_prefix="domain",
    key_param_name="domain_id",
)
async def update_domain(
    db: AsyncSession, domain_id: str | UUID4, domain: schemas.DomainCreate
) -> Optional[models.Domain]:
    domain_db = await db.get(models.Domain, domain_id)
    if domain_db:
        try:
            q = (
                update(models.Domain)
                .where(models.Domain.id == domain_id)
                .values(long_name=domain.long_name, short_name=domain.short_name)
            )
            await db.execute(q)
            await db.commit()
            await db.refresh(domain_db)
            return domain_db
        except IntegrityError:
            await db.rollback()
            return domain_db
    return None


@redis_cache(
    key_prefix="password",
    session_factory=SessionLocal,
    schema=schemas.Password,
    key_param_name="password_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_password(
    db: AsyncSession, password_id: str | UUID4
) -> Optional[models.Password]:
    return await db.get(models.Password, password_id)


async def get_passwords(
    db: AsyncSession, search: str = "", offset: int = 0, limit: int = 10
) -> Iterable[models.Password]:
    q = select(models.Password)
    if search:
        q = q.filter(models.Password.password.ilike(f"%{search}%"))
    result = await db.execute(q.offset(offset).limit(limit))
    return result.scalars().unique().all()


async def get_passwords_paged(
    db: AsyncSession, filters: filters.PasswordFilter
) -> Page[models.Password]:
    q: Select = select(models.Password)
    q = q.outerjoin(models.Password.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.Password.id)
    return await paginate(db, q)


async def get_kerberos_paged(
    db: AsyncSession, search: str = ""
) -> Page[models.Kerberos]:
    q = select(models.Kerberos)
    if search:
        q = q.filter(models.Kerberos.client.ilike(f"%{search}%"))
    return await paginate(db, q.order_by(models.Kerberos.time_created.desc()))


@redis_cache(
    key_prefix="kerberos",
    session_factory=SessionLocal,
    schema=schemas.Kerberos,
    key_param_name="kerberos_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_kerberos(
    db: AsyncSession, kerberos_id: str | UUID4
) -> Optional[models.Kerberos]:
    return await db.get(models.Kerberos, kerberos_id)


@redis_cache(
    key_prefix="credential",
    session_factory=SessionLocal,
    schema=schemas.Credential,
    key_param_name="credential_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_credential(
    db: AsyncSession, credential_id: str | UUID4
) -> Optional[models.Credential]:
    return await db.get(models.Credential, credential_id)


async def get_credentials(
    db: AsyncSession,
    filters: filters.CredentialFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Credential]:
    q: Select = select(models.Credential)
    q = q.outerjoin(models.Credential.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def search_credentials(
    db: AsyncSession, offset: int = 0, limit: int = 10
) -> Iterable[models.Credential]:
    result = await db.execute(select(models.Credential).offset(offset).limit(limit))
    return result.scalars().unique().all()


async def get_credentials_paged(
    db: AsyncSession, filters: filters.CredentialFilter
) -> Page[models.Credential]:
    q: Select = select(models.Credential)
    q = q.outerjoin(
        models.LabeledItem,
        onclause=models.Credential.id == models.LabeledItem.credential_id,
    )
    q = q.outerjoin(
        models.Label, onclause=models.LabeledItem.label_id == models.Label.id
    )
    if filters.domain:
        q = q.select_from(models.Credential).join(
            models.Domain, onclause=models.Credential.domain_id == models.Domain.id
        )
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.Credential.id)
    return await paginate(db, q)


async def create_credential(
    db: AsyncSession, credential: schemas.CredentialCreate
) -> models.Credential:
    credential_dict = credential.model_dump()
    credential_dict.pop("mark_owned", None)
    db_credential = models.Credential(**credential_dict)
    db.add(db_credential)
    await db.commit()
    await db.refresh(db_credential)
    await send_event(schemas.Event.credential, schemas.EventType.new, db_credential.id)
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
            models.Label, onclause=models.LabeledItem.label_id == models.Label.id
        )
    )
    q = filters.filter(q)  # type: ignore

    if filters.domain:
        q = q.select_from(models.Credential).join(
            models.Domain, onclause=models.Credential.domain_id == models.Domain.id
        )

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in ["username"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Credential, field), field, field
        )
        result.append(res)

    if not filters.domain:
        q = q.select_from(models.Credential).join(
            models.Domain, onclause=models.Credential.domain_id == models.Domain.id
        )
    q = q.add_columns(models.Domain.long_name)
    q = q.group_by(models.Domain.long_name)
    q = q.order_by(desc("count_1"))

    options: list[schemas.FilterOption] = []
    res = await db.execute(q)
    for entry in res.unique().all():
        if entry[1] or entry[1] == False:
            options.append(schemas.FilterOption(name=str(entry[1]), count=entry[0]))

    result.append(
        schemas.Filter(
            name="domain",
            icon="",
            type="options",
            options=options,
            query_name="domain__long_name",
        )
    )

    return result


@redis_cache(
    key_prefix="proxy",
    session_factory=SessionLocal,
    schema=schemas.Proxy,
    key_param_name="proxy_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_proxy(db: AsyncSession, proxy_id: str | UUID4) -> models.Proxy | None:
    return await db.get(models.Proxy, proxy_id)


async def get_proxies_paged(
    db: AsyncSession, filters: filters.ProxyFilter
) -> Page[models.Proxy]:
    q: Select = select(models.Proxy)
    q = q.outerjoin(models.Proxy.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.Proxy.id)
    return await paginate(db, q)


async def get_proxies(
    db: AsyncSession,
    filters: filters.ProxyFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Proxy]:
    q: Select = select(models.Proxy)
    q = q.outerjoin(models.Proxy.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_proxy_filters(db: AsyncSession, filters: filters.ProxyFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Proxy.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in ["host", "type", "status", "remote_hostname"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Proxy, field), field, field
        )
        result.append(res)

    return result


async def create_proxy(db: AsyncSession, proxy: schemas.ProxyCreate) -> models.Proxy:
    db_proxy = models.Proxy(**proxy.model_dump())
    db.add(db_proxy)
    await db.commit()
    await db.refresh(db_proxy)
    await send_event(schemas.Event.proxy, schemas.EventType.new, db_proxy.id)
    return db_proxy


@redis_cache(
    key_prefix="proxy_job",
    session_factory=SessionLocal,
    schema=schemas.ProxyJob,
    key_param_name="job_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_proxy_job(
    db: AsyncSession, job_id: str | UUID4
) -> Optional[models.ProxyJob]:
    return await db.get(models.ProxyJob, job_id)


@redis_cache_invalidate(
    key_prefix="proxy_job",
    key_param_name="job_id",
)
async def update_proxy_job(
    db: AsyncSession, job_id: str | UUID4, job: schemas.ProxyJobCreate
) -> Optional[models.ProxyJob]:
    values = job.model_dump()
    input_files = values.pop("input_files")
    q = update(models.ProxyJob).where(models.ProxyJob.id == job_id).values(**values)
    await db.execute(q)
    await db.commit()
    await delete_input_files(db, proxy_job_id=job_id)
    for input_file in input_files:
        await create_input_file(db, input_file, proxy_job_id=job_id)
    proxy_job = await db.get(models.ProxyJob, job_id)
    await send_event(schemas.Event.proxy_job, schemas.EventType.update, proxy_job.id)
    if proxy_job and proxy_job.playbook_id:
        await send_update_playbook(proxy_job.playbook_id, "updated_proxy_job", str(proxy_job.id))
    return proxy_job


@redis_cache_invalidate(
    key_prefix="proxy_job",
    key_param_name="job_id",
)
async def update_proxy_job_status(
    db: AsyncSession, status: str | None, job_id: str | UUID4, exit_code: int = 0
) -> Optional[models.ProxyJob]:
    job = await db.get(models.ProxyJob, job_id)
    if job:
        if status == schemas.Status.started:
            job.time_started = func.now()
        if status == schemas.Status.completed:
            job.time_completed = func.now()
        job.status = status or ""
        job.exit_code = exit_code
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job


async def get_proxy_jobs_paged(
    db: AsyncSession, filters: filters.SocksJobFilter
) -> Page[models.ProxyJob]:
    q: Select = select(models.ProxyJob)
    q = q.outerjoin(models.ProxyJob.labels)
    q = filters.filter(q)  # type: ignore
    try:
        q = filters.sort(q)  # type: ignore
    except NotImplementedError:
        pass
    q = q.group_by(models.ProxyJob.id)
    return await paginate(db, q)


async def get_proxy_jobs(
    db: AsyncSession,
    filters: filters.SocksJobFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.ProxyJob]:
    q: Select = (
        select(models.ProxyJob)
        .outerjoin(models.ProxyJob.labels)
        .group_by(models.ProxyJob.id)
    )
    q = filters.filter(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    q = q.order_by(models.ProxyJob.time_created.desc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def update_socks_task_summary(
    db, socks_task_id: str | UUID4, summary: str, status: str
) -> None:
    q = (
        update(models.ProxyJob)
        .where(models.ProxyJob.id == socks_task_id)
        .values(processing_status=status, ai_summary=summary)
    )
    await db.execute(q)
    await db.commit()


async def delete_input_files(
    db: AsyncSession,
    proxy_job_id: str | UUID4 | None = None,
    c2_job_id: str | UUID4 | None = None,
) -> None:
    q = delete(models.InputFile)
    if proxy_job_id:
        q = q.where(models.InputFile.proxy_job_id == proxy_job_id)
    elif c2_job_id:
        q = q.where(models.InputFile.c2_job_id == c2_job_id)
    else:
        return
    await db.execute(q)
    await db.commit()


async def create_input_file(
    db: AsyncSession,
    file_id: str,
    proxy_job_id: str | UUID4 | None = None,
    c2_job_id: str | UUID4 | None = None,
) -> models.InputFile:
    input_db = models.InputFile(
        file_id=file_id, c2_job_id=c2_job_id, proxy_job_id=proxy_job_id
    )
    db.add(input_db)
    await db.commit()
    await db.refresh(input_db)
    return input_db


async def create_proxy_job(
    db: AsyncSession, proxy_job: schemas.ProxyJobCreate
) -> models.ProxyJob:
    entries: dict[str, Any] = proxy_job.model_dump()
    input_files = entries.pop("input_files")
    db_proxy_job = models.ProxyJob(**entries)
    db_proxy_job.status = schemas.Status.created
    db.add(db_proxy_job)
    await db.commit()

    for input_file in input_files:
        await create_input_file(db, input_file, proxy_job_id=str(db_proxy_job.id))

    await send_event(schemas.Event.proxy_job, schemas.EventType.new, db_proxy_job.id)
    await db.refresh(db_proxy_job)
    return db_proxy_job


async def create_proxy_job_output(
    db: AsyncSession, output: schemas.ProxyJobOutputCreate
) -> None:
    proxy_job_output = models.ProxyJobOutput()
    proxy_job_output.output = output.output
    proxy_job_output.job_id = output.job_id
    db.add(proxy_job_output)
    await db.commit()
    await send_event(
        schemas.Event.proxy_job_output, schemas.EventType.new, proxy_job_output.id
    )


async def get_proxy_job_output_paged(
    db: AsyncSession, job_id: str = "", type: str = ""
) -> Page[models.ProxyJobOutput]:
    q = select(models.ProxyJobOutput)
    if job_id:
        q = q.where(models.ProxyJobOutput.job_id == job_id)
    if type:
        q = q.where(models.ProxyJobOutput.output_type == type)
    return await paginate(db, q.order_by(models.ProxyJobOutput.created_at.asc()))


async def get_proxy_job_output(
    db: AsyncSession, job_id: str | uuid.UUID = "", type: str = ""
) -> Iterable[models.ProxyJobOutput]:
    q = select(models.ProxyJobOutput)
    if job_id:
        q = q.where(models.ProxyJobOutput.job_id == job_id)
    if type:
        q = q.where(models.ProxyJobOutput.output_type == type)
    q = q.order_by(models.ProxyJobOutput.created_at.asc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_manual_timeline_tasks(
    db: AsyncSession, processing_status: str
) -> Iterable[models.ManualTimelineTask]:
    q = select(models.ManualTimelineTask)
    q = q.where(models.ManualTimelineTask.processing_status == processing_status)
    q = q.order_by(models.ManualTimelineTask.time_completed.asc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def update_manual_timeline_summary(
    db, manuel_task_id: str | UUID4, summary: str, status: str
) -> None:
    q = (
        update(models.ManualTimelineTask)
        .where(models.ManualTimelineTask.id == manuel_task_id)
        .values(processing_status=status, ai_summary=summary)
    )
    await db.execute(q)
    await db.commit()


async def add_file(
    db: AsyncSession,
    filename: str,
    bucket: str,
    path: str,
    filetype: str = "",
    job_id: str | None = None,
    id: str | uuid.UUID | None = None,
    c2_implant_id: str | uuid.UUID | None = None,
    c2_task_id: str | uuid.UUID | None = None,
) -> models.File:
    file = models.File(
        id=id,
        job_id=job_id,
        filename=filename,
        bucket=bucket,
        path=path,
        filetype=filetype,
        c2_implant_id=c2_implant_id,
        c2_task_id=c2_task_id,
    )
    db.add(file)
    await db.commit()
    await db.refresh(file)
    await send_event(schemas.Event.file, schemas.EventType.new, file.id)
    return file


@redis_cache_invalidate(
    key_prefix="file",
    key_param_name="file_id",
)
async def update_file(
    db: AsyncSession, file_id: str | uuid.UUID, file: schemas.FileUpdate
) -> None:
    q = update(models.File).where(models.File.id == file_id).values(**file.model_dump())
    await db.execute(q)
    await db.commit()
    await send_event(schemas.Event.file, schemas.EventType.update, str(file_id))


@redis_cache_invalidate(
    key_prefix="file",
    key_param_name="file_id",
)
async def update_file_path(
    db: AsyncSession, file_id: str | uuid.UUID, path: str
) -> None:
    q = update(models.File).where(models.File.id == file_id).values(path=path)
    await db.execute(q)
    await db.commit()
    await send_event(schemas.Event.file, schemas.EventType.update, str(file_id))


@redis_cache(
    key_prefix="file",
    session_factory=SessionLocal,
    schema=schemas.File,
    key_param_name="file_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_file(db: AsyncSession, file_id: str | uuid.UUID) -> Optional[models.File]:
    return await db.get(models.File, file_id)


async def get_files(
    db: AsyncSession,
    job_id: str | UUID4 = "",
    search: str = "",
    filetype: str = "",
) -> Iterable[models.File]:
    q = select(models.File)
    if job_id:
        q = q.where(models.File.job_id == job_id)
    if filetype:
        q = q.where(models.File.filetype == filetype)
    if search:
        q = q.where(models.File.filename.ilike(f"%{search}%"))
    result = await db.execute(q)
    return result.unique().scalars().all()


async def get_files_paged(
    db: AsyncSession,
    file_filters: filters.FileFilter,
) -> Page[models.File]:
    q: Select = select(models.File)
    q = q.outerjoin(models.File.labels)
    q = file_filters.filter(q)  # type: ignore
    try:
        q = file_filters.sort(q)  # type: ignore
    except NotImplementedError:
        pass
    q = q.group_by(models.File.id)
    return await paginate(db, q)


async def get_label_names(
    db: AsyncSession, label_ids: list[str]
) -> dict[str, models.Label]:
    q = select(models.Label).where(models.Label.id.in_(label_ids))
    labels = {}
    result = await db.execute(q)
    for entry in result.scalars().unique().all():
        labels[str(entry.id)] = entry
    return labels


async def get_file_filters(
    db: AsyncSession,
    file_filters: filters.FileFilter,
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.File.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = file_filters.filter(q)  # type: ignore

    ft_entry = await create_filter_for_column(
        db, q, models.File.filetype, "filetype", "filetype"
    )
    result.append(ft_entry)

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    return result


async def get_socks_job_filters(
    db: AsyncSession,
    filters: filters.SocksJobFilter,
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.ProxyJob.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    for entry in ["command", "status"]:
        ft_entry = await create_filter_for_column(
            db, q, getattr(models.ProxyJob, entry), entry, entry
        )
        result.append(ft_entry)

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    return result


async def create_filter_for_column(
    db: AsyncSession,
    q: Select,
    column: InstrumentedAttribute,
    name: str,
    query_name: str,
) -> schemas.Filter:
    ft_q = q.add_columns(column)
    ft_q = ft_q.group_by(column)
    ft_q = ft_q.order_by(desc("count_1"))

    result = await db.execute(ft_q)

    options: list[schemas.FilterOption] = []

    for entry in result.unique().all():
        if entry[1] or entry[1] == False:
            options.append(schemas.FilterOption(name=str(entry[1]), count=entry[0]))

    ft_entry = schemas.Filter(
        name=name, icon="", type="options", options=options, query_name=query_name
    )
    return ft_entry


async def search_files(
    db: AsyncSession,
    file_filters: filters.FileFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.File]:
    q = select(models.File).outerjoin(models.LabeledItem).outerjoin(models.Label)
    q = file_filters.filter(q)
    result = await db.execute(q.offset(offset).limit(limit))
    return result.scalars().unique().all()


@redis_cache_invalidate(
    key_prefix="file",
    key_param_name="file_id",
)
async def update_file_type(
    db: AsyncSession, file_id: str | uuid.UUID, filetype: schemas.FileType | str | None
) -> Optional[models.File]:
    q = update(models.File).where(models.File.id == file_id).values(filetype=filetype)
    await db.execute(q)
    await db.commit()
    await send_event(schemas.Event.file, schemas.EventType.update, str(file_id))


async def update_or_create_proxy(
    db: AsyncSession,
    proxy: schemas.ProxyCreate,
) -> Tuple[bool, models.Proxy]:
    q = (
        select(models.Proxy)
        .where(models.Proxy.type == proxy.type.value)
        .where(models.Proxy.host == proxy.host)
        .where(models.Proxy.port == proxy.port)
    )

    if proxy.c2_server_id:
        q = q.where(models.Proxy.c2_server_id == proxy.c2_server_id)
    if proxy.internal_id:
        q = q.where(models.Proxy.internal_id == proxy.internal_id)
    if proxy.c2_task_id:
        q = q.where(models.Proxy.c2_task_id == proxy.c2_task_id)
    if proxy.c2_implant_id:
        q = q.where(models.Proxy.c2_implant_id == proxy.c2_implant_id)

    new = False
    resp = await db.execute(q)
    try:
        proxy_db = resp.scalars().unique().one()
        new = False
    except exc.NoResultFound:
        proxy_db = models.Proxy(**proxy.model_dump())
        proxy_db.type = proxy.type.value
        await send_event(schemas.Event.proxy, schemas.EventType.new, proxy_db.id)
        new = True

    proxy_db.status = proxy.status.value
    db.add(proxy_db)
    await db.commit()
    await db.refresh(proxy_db)
    return new, proxy_db


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, models.User)


def filter_shuffle(seq):
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq


env = SandboxedEnvironment(
    enable_async=True,
    autoescape=False,
    loader=PackageLoader("harbinger.job_templates", "templates"),
    extensions=[do],
)
env.filters["shuffle"] = filter_shuffle


async def preview_chain_from_template(
    db: AsyncSession, chain: schemas.PlaybookTemplate, arguments: dict
) -> dict:
    labels = await get_labeled_items_list(
        db,
        c2_implant_id=arguments.get("c2_implant", None),
        retrieve_parents=True,
    )
    await _process_dynamic_argument_ids(db, arguments)

    result = dict(steps="", valid=False, errors="", steps_errors="")
    try:
        value_template = env.from_string(chain.steps or "")
        steps_str = await value_template.render_async(**arguments, labels=labels)
        steps_dict = yaml.safe_load(steps_str)

        StepValidator = TypeAdapter(List[schemas.Step])
        result = dict(steps=steps_str, valid=False)
        try:
            steps: List[schemas.Step] = StepValidator.validate_python(steps_dict)
            result["valid"] = True
        except ValidationError as e:
            result["steps_errors"] = e.json()
        except Exception:
            pass
    except jinja2.exceptions.TemplateSyntaxError as e:
        result["errors"] = str(e)
    except jinja2.exceptions.UndefinedError as e:
        result["errors"] = str(e)
    except Exception as e:
        result["errors"] = str(e)

    return result


async def _process_dynamic_argument_ids(db: AsyncSession, arguments: dict[str, Any]):
    """
    Helper function to dynamically process arguments ending with '_id<number>'
    and replace them with the corresponding model instance, preserving the number.
    """
    
    # Define a mapping of base prefixes to their corresponding models
    # This dictionary now contains only the base names without numbers
    model_mappings = {
        "credential": models.Credential,
        "c2_implant": models.C2Implant,
        "kerberos": models.Kerberos,
        "file": models.File,
    }

    arguments_to_process = list(arguments.keys()) # Create a copy to iterate safely
    
    for arg_key in arguments_to_process:
        for base_prefix, model_class in model_mappings.items():
            # Use regex to match patterns like "credential_id", "credential_id1", "file_id5", etc.
            match = re.fullmatch(rf"{base_prefix}_id(\d*)", arg_key)
            if match:
                suffix = match.group(1) # This will be "" for "credential_id" or "1" for "credential_id1"
                item_id = arguments[arg_key]
                item = await db.get(model_class, item_id)
                if item:
                    new_key = f"{base_prefix}{suffix}"
                    arguments[new_key] = item
                break


async def create_chain_from_template(
    db: AsyncSession, chain: schemas.PlaybookTemplate, arguments: dict
) -> models.Playbook:
    labels = await get_labeled_items_list(
        db,
        c2_implant_id=arguments.get("c2_implant", None),
        retrieve_parents=True,
    )
    await _process_dynamic_argument_ids(db, arguments)

    value_template = env.from_string(chain.steps or "")
    steps_str = await value_template.render_async(**arguments, labels=labels)
    steps_dict = yaml.safe_load(steps_str)

    StepValidator = TypeAdapter(List[schemas.Step])
    steps: List[schemas.Step] = StepValidator.validate_python(steps_dict)

    playbook_obj = models.Playbook(
        playbook_name=chain.name,
        status=schemas.Status.created,
        arguments=json.loads(json.dumps(arguments, default=lambda o: "")),
        steps=len(steps),
        completed=0,
        playbook_template_id=chain.id,
    )
    db.add(playbook_obj)
    await db.commit()
    await db.refresh(playbook_obj)
    playbook_id = playbook_obj.id
    count = 1

    for step in steps:
        step_delay = timedelta(seconds=step.delay or 0)
        job = None
        proxy_job_id = None
        c2_job_id = None
        extra_args = dict()
        for arg in step.args or []:
            extra_args[arg.name] = arg.value

        if step.type == schemas.C2Type.proxy:
            from harbinger.job_templates.proxy import PROXY_JOB_BASE_MAP
            args = {**arguments, **extra_args}
            proxy_job = PROXY_JOB_BASE_MAP[step.name](**args)
            job_db = await create_proxy_job(
                db,
                schemas.ProxyJobCreate(
                    command=await proxy_job.generate_command(),
                    proxy_id=arguments.get("proxy_id", None),
                    arguments=await proxy_job.generate_arguments(db),
                    input_files=await proxy_job.files(db),
                    socks_server_id=proxy_job.socks_server_id,
                    tmate=step.tmate,
                    asciinema=step.asciinema,
                    proxychains=step.proxychains,
                    # add_labels=getattr(job.Settings, "add_labels", None),
                ),
            )
            proxy_job_id = job_db.id
        elif step.type == schemas.C2Type.c2:
            from harbinger.job_templates.schemas import C2_JOB_BASE_MAP

            job = C2_JOB_BASE_MAP[step.name](**{**arguments, **extra_args})
            job_db = await create_c2_job(
                db,
                schemas.C2JobCreate(
                    command=job.Settings.command,
                    arguments=await job.generate_arguments(db),
                    input_files=await job.files(db),
                    playbook_id=str(playbook_id),
                    c2_implant_id=job.c2_implant_id,
                    add_labels=getattr(job.Settings, "add_labels", None),
                ),
            )
            c2_job_id = job_db.id

        step_db = await add_step(
            db,
            step=schemas.ChainStepCreate(
                playbook_id=str(playbook_id),
                number=count,
                delay=step_delay,
                proxy_job_id=proxy_job_id,
                c2_job_id=c2_job_id,
                label=step.label,
                depends_on=step.depends_on,
            ),
            add_depends_on=chain.add_depends_on,
        )
        if step.modifiers:
            for modifier in step.modifiers:
                data = modifier.model_dump()
                data["playbook_step_id"] = step_db.id
                await create_playbook_step_modifier(
                    db, schemas.PlaybookStepModifierCreate(**data)
                )
        count += 1

    await db.commit()
    await db.refresh(playbook_obj)
    await send_event(schemas.Event.playbook, schemas.EventType.new, playbook_obj.id)
    return playbook_obj


async def create_chain(
    db: AsyncSession, chain: schemas.ProxyChainCreate
) -> models.Playbook:
    db_chain = models.Playbook(**chain.model_dump())
    db_chain.status = schemas.Status.created
    db_chain.steps = 0
    db_chain.completed = 0
    db.add(db_chain)
    await db.commit()
    await db.refresh(db_chain)
    await send_event(schemas.Event.playbook, schemas.EventType.new, db_chain.id)
    return db_chain


async def clone_chain(
    db: AsyncSession, chain: models.Playbook | schemas.ProxyChainGraph
) -> models.Playbook:
    new_chain = models.Playbook(
        playbook_name=f"Clone of {chain.playbook_name}",
        description=chain.description,
        status=schemas.Status.created,
        arguments=chain.arguments,
        steps=chain.steps,
        completed=0,
    )
    db.add(new_chain)
    await db.commit()
    await db.refresh(new_chain)

    steps = await get_playbook_steps(db, 0, 10000000, str(chain.id))
    for step in steps:
        await clone_chain_step(db, step, str(new_chain.id))

    await send_event(schemas.Event.playbook, schemas.EventType.new, new_chain.id)
    await db.refresh(new_chain)
    return new_chain


async def get_playbooks(
    db: AsyncSession,
    filters: filters.PlaybookFilter,
    offset: int = 0,
    limit: int = 0,
) -> Iterable[models.Playbook]:
    q: Select = (
        select(models.Playbook)
        .outerjoin(models.Playbook.labels)
        .group_by(models.Playbook.id)
    )
    q = q.outerjoin(models.Playbook.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


@redis_cache_invalidate(
    key_prefix="playbook",
    key_param_name="playbook_id",
)
async def update_chain(
    db: AsyncSession, playbook_id: str, chain: schemas.ProxyChainCreate
) -> Optional[models.Playbook]:
    db_chain = await db.get(models.Playbook, id)
    if db_chain:
        db_chain.playbook_name = chain.playbook_name  # type: ignore
        db_chain.description = chain.description  # type: ignore
        db.add(db_chain)
        await db.commit()
        await db.refresh(db_chain)
    await send_update_playbook(playbook_id, "updated_chain")
    await send_event(schemas.Event.playbook, schemas.EventType.update, playbook_id)
    return db_chain


async def send_update_playbook(playbook_id: str, event_name: str, id: str = ""):
    msg = messages_pb2.Event(event=event_name, id=id)
    await redis.publish(f"playbook_stream_{playbook_id}", msg.SerializeToString())


async def get_playbooks_paged(
    db: AsyncSession, filters: filters.PlaybookFilter
) -> Page[models.Playbook]:
    q: Select = select(models.Playbook)
    q = q.outerjoin(models.Playbook.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.Playbook.id)
    return await paginate(db, q)


async def get_playbooks_filters(db: AsyncSession, filters: filters.PlaybookFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Playbook.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in ["playbook_name", "status"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Playbook, field), field, field
        )
        result.append(res)

    return result


@redis_cache(
    key_prefix="playbook",
    session_factory=SessionLocal,
    schema=schemas.ProxyChainGraph,  # Ensure this schema exists and matches model
    key_param_name="id",  # Key parameter is named 'id' here
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_playbook(db: AsyncSession, id: UUID4 | str) -> Optional[models.Playbook]:
    return await db.get(models.Playbook, id)


async def get_chains(db: AsyncSession) -> Page[models.Playbook]:
    return await paginate(
        db, select(models.Playbook).order_by(models.Playbook.time_created.desc())
    )


async def get_chain_steps_paged(
    db: AsyncSession, playbook_id: str = ""
) -> Page[models.PlaybookStep]:
    q = select(models.PlaybookStep)
    if playbook_id:
        q = q.where(models.PlaybookStep.playbook_id == playbook_id)
    q = q.order_by(models.PlaybookStep.number.asc())
    return await paginate(db, q)


async def get_playbook_steps(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 10,
    playbook_id: str | uuid.UUID = "",
) -> Iterable[models.PlaybookStep]:
    q = select(models.PlaybookStep)
    if playbook_id:
        q = q.where(models.PlaybookStep.playbook_id == playbook_id)
    q = q.order_by(models.PlaybookStep.number.asc())
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_chain_step(
    db: AsyncSession, playbook_id: str, number: int
) -> Optional[models.PlaybookStep]:
    q = await db.execute(
        select(models.PlaybookStep)
        .where(models.PlaybookStep.playbook_id == playbook_id)
        .where(models.PlaybookStep.number == number)
    )
    try:
        return q.scalars().unique().one()
    except exc.NoResultFound:
        return None


async def get_chain_step_by_id(
    db: AsyncSession, step_id: str
) -> Optional[models.PlaybookStep]:
    return await db.get(models.PlaybookStep, step_id)


async def clone_chain_step(
    db: AsyncSession,
    step: models.PlaybookStep,
    playbook_id: str,
    update_label: bool = False,
) -> models.PlaybookStep:
    to_add = schemas.ChainStepCreate(
        playbook_id=playbook_id,
        number=step.number + 1,
        delay=step.delay,
        label=step.label,
        depends_on=step.depends_on,
    )
    if step.proxy_job_id:
        proxy_job = await clone_proxy_job(db, step.proxy_job_id, playbook_id)
        if proxy_job:
            to_add.proxy_job_id = proxy_job.id
    if step.c2_job_id:
        new_job = await clone_c2_job(db, step.c2_job_id, playbook_id)
        if new_job:
            to_add.c2_job_id = new_job.id

    if update_label:
        highest = await get_highest_step(db, step.playbook_id)
        to_add.number = (highest or 0) + 1
        to_add.label = to_excel(to_add.number)

    new_step = await add_step(
        db,
        to_add,
        add_depends_on=False,
    )
    if step.step_modifiers:
        for step_modifier in step.step_modifiers:
            await create_playbook_step_modifier(
                db,
                schemas.PlaybookStepModifierCreate(
                    input_path=step_modifier.input_path,
                    playbook_step_id=new_step.id,
                    output_path=step_modifier.output_path,
                    regex=step_modifier.regex,
                ),
            )
    if playbook_id:
        await send_update_playbook(playbook_id, "new_step", id=str(new_step.id))
    return new_step


async def clone_c2_job(
    db: AsyncSession, c2_job_id: str, playbook_id: str | None = None
) -> models.C2Job | None:
    c2_job = await db.get(models.C2Job, c2_job_id)
    if c2_job:
        new_c2_job = await create_c2_job(
            db,
            schemas.C2JobCreate(
                command=c2_job.command,
                arguments=c2_job.arguments,
                c2_implant_id=c2_job.c2_implant_id,
                input_files=[str(file.id) for file in c2_job.input_files],
                add_labels=list(c2_job.add_labels or []),
                playbook_id=playbook_id,
            ),
        )
        return new_c2_job


async def clone_proxy_job(
    db: AsyncSession, proxy_job_id: str, playbook_id: str | None = None
) -> models.ProxyJob | None:
    proxy_job = await db.get(models.ProxyJob, proxy_job_id)
    if proxy_job:
        new_proxy_job = await create_proxy_job(
            db,
            schemas.ProxyJobCreate(
                credential_id=proxy_job.credential_id,
                command=proxy_job.command,
                proxy_id=proxy_job.proxy_id,
                arguments=proxy_job.arguments,
                input_files=[str(file.id) for file in proxy_job.input_files],
                playbook_id=playbook_id,
                asciinema=proxy_job.asciinema,
                tmate=proxy_job.tmate,
                proxychains=proxy_job.proxychains,
                env=proxy_job.env,
                socks_server_id=proxy_job.socks_server_id,
            ),
        )
        return new_proxy_job


@redis_cache_invalidate(
    key_prefix="playbook",
    key_param_name="playbook_id",
)
async def update_chain_status(
    db: AsyncSession, status: str, playbook_id: str | UUID4, completed: int
) -> Optional[models.Playbook]:
    chain = await db.get(models.Playbook, playbook_id)
    if chain:
        if status == schemas.Status.started:
            chain.time_started = func.now()
        if status == schemas.Status.completed:
            chain.time_completed = func.now()
        chain.status = status
        chain.completed = completed
        db.add(chain)
        await db.commit()
        await db.refresh(chain)
        msg = messages_pb2.Event(event="playbook_status", chain_status=status)
        await redis.publish(f"playbook_stream_{playbook_id}", msg.SerializeToString())
        await update_action_status(db, status, playbook_id)
        await send_event(schemas.Event.playbook, schemas.EventType.update, playbook_id)
        return chain


async def update_action_status(
    db: AsyncSession, status: str, playbook_id: str | UUID4
) -> None:
    q = (
        update(models.Action)
        .values(status=status)
        .where(models.Playbook.id == playbook_id)
        .where(
            models.Playbook.playbook_template_id
            == models.ActionPlaybook.playbook_template_id
        )
        .where(models.Action.id == models.ActionPlaybook.action_id)
    )
    if status == schemas.Status.running:
        q = q.values(time_started=func.now())
    if status == schemas.Status.completed:
        q = q.values(time_completed=func.now())
    await db.execute(q)
    await db.commit()


@redis_cache_invalidate(
    key_prefix="playbook_step",
    key_param_name="step_id",
)
async def update_step_status(
    db: AsyncSession, status: str, step_id: str | uuid.UUID
) -> Optional[models.PlaybookStep]:
    step = await db.get(models.PlaybookStep, step_id)
    if step:
        if status in [
            schemas.Status.started,
            schemas.Status.starting,
            schemas.Status.queued,
            schemas.Status.scheduled,
        ]:
            step.time_started = func.now()
        if status in [schemas.Status.completed, schemas.Status.error]:
            step.time_completed = func.now()
        step.status = status
        db.add(step)
        await db.commit()
        await db.refresh(step)
        msg = messages_pb2.Event(event="step_status", chain_status=status)
        await redis.publish(
            f"playbook_stream_{step.playbook_id}", msg.SerializeToString()
        )

        return step


async def get_chain_step_by_proxy_job_id(
    db: AsyncSession, job_id: str
) -> Optional[models.PlaybookStep]:
    q = await db.execute(
        select(models.PlaybookStep).where(models.PlaybookStep.proxy_job_id == job_id)
    )
    try:
        return q.scalars().unique().one()
    except exc.NoResultFound:
        return None


async def get_chain_step_by_c2_job_id(
    db: AsyncSession, job_id: str | UUID4
) -> Optional[models.PlaybookStep]:
    q = await db.execute(
        select(models.PlaybookStep).where(models.PlaybookStep.c2_job_id == job_id)
    )
    try:
        return q.scalars().unique().one()
    except exc.NoResultFound:
        return None

async def update_playbook_steps(db: AsyncSession, playbook_id: str | uuid.UUID) -> None:
    playbook = await get_playbook(playbook_id)
    if playbook:
        count = 0
        steps = await get_playbook_steps(db, 0, 100000, playbook_id)
        for step in steps:
            count += 1
            step.number = count
            db.add(step)

        await db.execute(update(models.Playbook).where(models.Playbook.id == playbook_id).values(steps=count))
        await db.commit()
        await send_event(schemas.Event.playbook, schemas.EventType.update, playbook_id)


async def delete_step(db: AsyncSession, step_id: str) -> None:
    db_step = await get_chain_step_by_id(db, step_id)
    if db_step:
        playbook_id = db_step.playbook_id
        await delete_input_files(db, db_step.proxy_job_id, db_step.c2_job_id)
        await db.execute(
            delete(models.PlaybookStep).where(models.PlaybookStep.id == step_id)
        )
        if db_step.proxy_job_id:
            await db.execute(
                delete(models.ProxyJob).where(
                    models.ProxyJob.id == db_step.proxy_job_id
                )
            )
        if db_step.c2_job_id:
            await db.execute(
                delete(models.C2Job).where(models.C2Job.id == db_step.c2_job_id)
            )

        await db.commit()
        if playbook_id:
            await update_playbook_steps(db, playbook_id)
            await send_update_playbook(playbook_id, "deleted_step", str(step_id))


def divmod_excel(n: int) -> Tuple[int, int]:
    a, b = divmod(n, 26)
    if b == 0:
        return a - 1, b + 26
    return a, b


def to_excel(num: int) -> str:
    chars = []
    while num > 0:
        num, d = divmod_excel(num)
        chars.append(string.ascii_uppercase[d - 1])
    return "".join(reversed(chars))


async def get_highest_step(db, playbook_id) -> int:
    q = (
        select(models.PlaybookStep.number)
        .where(models.PlaybookStep.playbook_id == playbook_id)
        .order_by(models.PlaybookStep.number.desc())
    )
    result = await db.execute(q.limit(1))
    return result.scalars().first()


async def add_step(
    db: AsyncSession, step: schemas.ChainStepCreate, add_depends_on: bool | None = True
) -> models.PlaybookStep:
    if not step.number:
        highest = await get_highest_step(db, step.playbook_id)
        step.number = (highest or 0) + 1
    if not step.label:
        step.label = to_excel(step.number)
    if add_depends_on and not step.depends_on and step.number > 1:
        step.depends_on = to_excel(step.number - 1)

    db_step = models.PlaybookStep(**step.model_dump())
    db_step.status = schemas.Status.created
    db.add(db_step)
    await db.commit()
    await db.refresh(db_step)
    if step.playbook_id:
        await update_playbook_steps(db, step.playbook_id)
        await send_update_playbook(step.playbook_id, "new_step", str(db_step.id))
    await send_event(schemas.Event.playbook_step, schemas.EventType.new, db_step.id)
    return db_step


@redis_cache_invalidate(
    key_prefix="playbook_step",
    key_param_name="step_id",
)
async def update_step(
    db: AsyncSession, step_id: str, step: schemas.ChainStepCreate
) -> Optional[models.PlaybookStep]:
    db_step = await get_chain_step_by_id(db, step_id)
    if db_step:
        db_step.number = step.number
        db_step.playbook_id = step.playbook_id
        db_step.proxy_job_id = step.proxy_job_id
        db_step.c2_job_id = step.c2_job_id
        db_step.delay = step.delay  # type: ignore
        db_step.execute_after = step.execute_after  # type: ignore
        db_step.label = step.label  # type: ignore
        db_step.depends_on = step.depends_on  # type: ignore
        db.add(db_step)
        await db.commit()
        if step.playbook_id:
            await update_playbook_steps(db, step.playbook_id)
            await send_update_playbook(step.playbook_id, "updated_step", str(db_step.id))
        await db.refresh(db_step)
        await send_event(
            schemas.Event.playbook_step, schemas.EventType.update, db_step.id
        )
        return db_step
    return None


async def get_c2_jobs_paged(
    db: AsyncSession, filters: filters.C2JobFilter
) -> Page[models.C2Job]:
    q: Select = select(models.C2Job)
    q = q.outerjoin(models.C2Job.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.C2Job.id)
    return await paginate(db, q)


async def get_c2_jobs_filters(db: AsyncSession, filters: filters.C2JobFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.C2Job.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in ["status", "command", "arguments"]:
        res = await create_filter_for_column(
            db, q, getattr(models.C2Job, field), field, field
        )
        result.append(res)

    return result


async def get_c2_jobs(
    db: AsyncSession, completed_only: bool = False
) -> Iterable[models.C2Job]:
    q = select(models.C2Job)
    if completed_only:
        q = q.where(models.C2Job.time_completed.isnot(None)).order_by(
            models.C2Job.time_completed.asc()
        )
    result = await db.execute(q)
    return result.scalars().unique().all()


async def create_c2_job(db: AsyncSession, job: schemas.C2JobCreate) -> models.C2Job:
    entries: dict[str, Any] = job.model_dump()
    input_files = entries.pop("input_files")
    db_obj = models.C2Job(**entries)
    db_obj.status = schemas.Status.created
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    for input_file in input_files or []:
        await create_input_file(db, input_file, c2_job_id=str(db_obj.id))
    await send_event(schemas.Event.c2_job, schemas.EventType.new, db_obj.id)
    return db_obj


@redis_cache(
    key_prefix="c2_job",
    session_factory=SessionLocal,
    schema=schemas.C2Job,  # Ensure this schema exists
    key_param_name="job_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_c2_job(db: AsyncSession, job_id: str | UUID4) -> Optional[models.C2Job]:
    return await db.get(models.C2Job, job_id)


@redis_cache_invalidate(
    key_prefix="c2_job",
    key_param_name="c2_job_id",
)
async def update_c2_job(
    db: AsyncSession, c2_job_id: str | UUID4, job: schemas.C2JobCreate
) -> Optional[models.C2Job]:
    values = job.model_dump()
    input_files = values.pop("input_files")
    q = update(models.C2Job).where(models.C2Job.id == c2_job_id).values(**values)
    await db.execute(q)
    await db.commit()
    await delete_input_files(db, c2_job_id=c2_job_id)
    for input_file in input_files:
        await create_input_file(db, input_file, c2_job_id=c2_job_id)

    c2_job = await db.get(models.C2Job, c2_job_id)
    if c2_job and c2_job.playbook_id:
        await send_update_playbook(c2_job.playbook_id, "updated_c2_job", str(c2_job_id))
    await send_event(schemas.Event.c2_job, schemas.EventType.update, c2_job_id)
    return c2_job


@redis_cache_invalidate(
    key_prefix="c2_job",
    key_param_name="c2_job_id",
)
async def update_c2_job_status(
    db: AsyncSession,
    c2_job_id: str | UUID4,
    status: str,
    message: str = "",
) -> None:
    values = dict(status=status)
    if message:
        values["message"] = message
    if status == schemas.Status.running:
        values["time_started"] = func.now()  # type: ignore
    if status == schemas.Status.completed or status == schemas.Status.error:
        values["time_completed"] = func.now()  # type: ignore
    q = update(models.C2Job).where(models.C2Job.id == c2_job_id).values(**values)
    await db.execute(q)
    await db.commit()
    await send_event(schemas.Event.c2_job, schemas.EventType.update, c2_job_id)


async def get_c2_job_status_by_task(
    db: AsyncSession,
    c2_task_id: str | UUID4 | None = None,
) -> Optional[models.C2Job]:
    q = select(models.C2Job)
    if c2_task_id:
        q = q.where(models.C2Job.c2_task_id == c2_task_id)
    result = await db.execute(q)
    return result.unique().scalar_one_or_none()


async def get_highest_process_number(db: AsyncSession, host_id: str | uuid.UUID) -> int:
    q = select(func.max(models.Process.number)).where(models.Process.host_id == host_id)
    result = await db.execute(q)
    return result.scalar_one_or_none() or 0


async def create_process(
    db: AsyncSession, process: schemas.ProcessCreate
) -> models.Process:
    process_db = models.Process(**process.model_dump())
    db.add(process_db)
    await db.commit()
    await db.refresh(process_db)
    await send_event(schemas.Event.process, schemas.EventType.new, process_db.id)
    return process_db


async def get_process_numbers(
    db: AsyncSession,
    host_id: str = "",
    c2_implant_id: str = "",
) -> Iterable[int]:
    q = select(models.Process.number)
    if host_id:
        q = q.where(models.Process.host_id == host_id)
    if c2_implant_id:
        q = q.where(models.Process.c2_implant_id == c2_implant_id)
    result = await db.execute(q.order_by(models.Process.number))
    return result.scalars().unique().all()


async def get_processes_paged(
    db: AsyncSession,
    host_id: str = "",
    c2_implant_id: str = "",
    number: int = 0,
    parent_process_id: str = "",
    only_top_processes: bool = False,
    labels_only: bool = False,
    search: str = "",
) -> Page[models.Process]:
    q = select(models.Process)
    if host_id:
        q = q.where(models.Process.host_id == host_id)
    if c2_implant_id:
        q = q.where(models.Process.c2_implant_id == c2_implant_id)
    if number:
        q = q.where(models.Process.number == number)
    if only_top_processes:
        q = q.where(models.Process.parent_process_id == 0)
    if parent_process_id:
        q = q.where(models.Process.parent_process_id == parent_process_id)
    if search:
        q = q.where(models.Process.name.ilike(f"%{search}%"))
    if labels_only:
        q = q.where(models.LabeledItem.process_id == models.Process.id)
    return await paginate(db, q.order_by(models.Process.process_id.asc()))


async def get_processes(
    db: AsyncSession,
    host_id: str = "",
    c2_implant_id: str = "",
    number: int = 0,
    parent_process_id: str = "",
    offset: int = 0,
    limit: int = 10,
    with_users_only: bool = False,
    only_top_processes: bool = False,
) -> Iterable[models.Process]:
    q = select(models.Process)
    if host_id:
        q = q.where(models.Process.host_id == host_id)
    if c2_implant_id:
        q = q.where(models.Process.c2_implant_id == c2_implant_id)
    if number:
        q = q.where(models.Process.number == number)
    if only_top_processes:
        q = q.where(models.Process.parent_process_id == 0)
    if parent_process_id:
        q = q.where(models.Process.parent_process_id == parent_process_id)
    if with_users_only:
        q = q.where(~(models.Process.user == ""))
    q = q.limit(limit).offset(offset)
    result = await db.execute(q.order_by(models.Process.process_id.asc()))
    return result.scalars().unique().all()


async def get_hosts_paged(
    db: AsyncSession,
    host_filters: filters.HostFilter,
) -> Page[models.Host]:
    q = select(models.Host).outerjoin(models.LabeledItem).outerjoin(models.Label)
    q = host_filters.filter(q)
    try:
        q = host_filters.sort(q)
    except NotImplementedError:
        pass
    q = q.group_by(models.Host.id)
    return await paginate(db, q)  # type: ignore


async def get_hosts(
    db: AsyncSession,
    filters: filters.HostFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Host]:
    q: Select = select(models.Host)
    q = q.outerjoin(models.Host.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_host_filters(
    db: AsyncSession,
    host_filters: filters.HostFilter,
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q = (
        select(func.count(models.Host.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = host_filters.filter(q)

    # labels
    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


async def get_labels_for_q(db: AsyncSession, q) -> list[schemas.Filter]:
    lq = q.group_by(models.LabeledItem.label_id)
    lq = lq.add_columns(models.LabeledItem.label_id)
    lq = lq.order_by(desc("count_1"))

    labels = await db.execute(lq)
    labels_list = list(labels.unique().all())
    label_options: list[schemas.FilterOption] = []

    label_names = await get_label_names(
        db, [str(entry[1]) for entry in labels_list if entry[1]]
    )

    for entry in labels_list:
        if entry[1]:
            label = label_names.get(str(entry[1]))
            if label:
                label_options.append(
                    schemas.FilterOption(
                        name=label.name, count=entry[0], color=label.color
                    )
                )
    lb_entry = schemas.Filter(
        name="labels",
        icon="",
        type="options",
        options=label_options,
        query_name="label__name__in",
        multiple=True,
    )
    return [lb_entry]


@redis_cache(
    key_prefix="host",
    session_factory=SessionLocal,
    schema=schemas.Host,  # Ensure this schema exists
    key_param_name="host_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_host(db: AsyncSession, host_id: str | uuid.UUID) -> Optional[models.Host]:
    return await db.get(models.Host, host_id)


async def get_or_create_host(
    db: AsyncSession,
    name: str,
    domain_id: str | uuid.UUID | None = None,
) -> Tuple[bool, models.Host]:
    """
    Searches the name and fqdn for the name of the host.
    If it is not found, creates a host with the name as either name or fqdn depending on the number of dots in the name.
    returns Tuple[bool, Host] with the first value indicating if the host was created.
    """
    created = False
    query = select(models.Host).where(
        or_(
            models.Host.name.ilike(name),
            models.Host.fqdn.ilike(name),
        )
    )
    if domain_id:
        query = query.where(
            or_(
                models.Host.domain_id == domain_id,
                models.Host.domain_id == None,
            )
        )

    q = await db.execute(query)
    host = q.scalars().unique().first()
    if not host:
        created = True
        host = models.Host()
        if domain_id:
            host.domain_id = domain_id
        if name.count(".") == 0:
            host.name = name
        else:
            host.fqdn = name
            if not domain_id:
                name, domain = name.split(".", 1)
                host.name = name
            domain = await get_or_create_domain(db, domain)
            host.domain_id = domain.id
            domain_id = domain.id
        db.add(host)
        try:
            await db.commit()
            await db.refresh(host)
            await send_event(schemas.Event.host, schemas.EventType.new, host.id)
        except exc.IntegrityError:
            await db.rollback()
            created, host = await get_or_create_host(db, name, domain_id)
    return created, host


@redis_cache_invalidate(
    key_prefix="host",
    key_param_name="host_id",
)
async def update_host(
    db: AsyncSession, host_id: str | uuid.UUID, host: schemas.HostBase
) -> Optional[models.Host]:
    q = (
        update(models.Host)
        .where(models.Host.id == host_id)
        .values(
            **host.model_dump(
                exclude_unset=True, exclude_defaults=True, exclude_none=True
            )
        )
    )
    await db.execute(q)
    await db.commit()
    await send_event(schemas.Event.host, schemas.EventType.update, host_id)
    return await db.get(models.Host, host_id)


@redis_cache_fixed_key(
    cache_key="job_statistics",
    session_factory=SessionLocal,  # Use your SessionLocal
    schema=schemas.StatisticsItems,
)
async def get_job_statistics(db: AsyncSession) -> dict:
    stats = {}
    q = select(models.ProxyJob.status, func.count(models.ProxyJob.id)).group_by(
        models.ProxyJob.status
    )
    result = await db.execute(q)
    for entry in result.all():
        if entry[0]:
            stats[entry[0]] = entry[1]
    q = select(models.C2Job.status, func.count(models.C2Job.id)).group_by(
        models.C2Job.status
    )
    result = await db.execute(q)
    for entry in result.all():
        if entry[0] in stats:
            stats[entry[0]] += entry[1]
        else:
            stats[entry[0]] = entry[1]

    return dict(items=[dict(key=key, value=value) for key, value in stats.items()])


@redis_cache_fixed_key(
    cache_key="implant_statistics",
    session_factory=SessionLocal,  # Use your SessionLocal
    schema=schemas.StatisticsItems,
)
async def get_implant_statistics(db: AsyncSession) -> dict:
    stats = {}
    q = select(models.C2Implant.payload_type, func.count(models.C2Implant.id)).group_by(
        models.C2Implant.payload_type
    )
    results = await db.execute(q)
    for entry in results.all():
        if entry[0]:
            stats[entry[0]] = entry[1]

    return dict(
        items=[
            dict(key=key, value=value, icon="question_mark")
            for key, value in stats.items()
        ]
    )


@redis_cache(
    key_prefix="playbook_template",
    session_factory=SessionLocal,
    schema=schemas.PlaybookTemplateView,  # Ensure this schema exists and matches model
    key_param_name="template_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_playbook_template(
    db: AsyncSession, template_id: str | uuid.UUID
) -> Optional[models.PlaybookTemplate]:
    return await db.get(models.PlaybookTemplate, template_id)


async def get_chain_templates(db: AsyncSession, filters: filters.PlaybookTemplateFilter) -> Iterable[models.PlaybookTemplate]:
    q: Select = select(models.PlaybookTemplate).outerjoin(
        models.PlaybookTemplate.labels
    )
    q = filters.filter(q)  # type: ignore
    try:
        q = filters.sort(q)  # type: ignore
    except NotImplementedError:
        pass
    q = q.group_by(models.PlaybookTemplate.id)
    if filters.search:
        if len(filters.search) == 36:
            q = q.where(
                or_(
                    models.PlaybookTemplate.name.ilike(f"%{filters.search}%"),
                    models.PlaybookTemplate.id == filters.search,
                )
            )
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_chain_templates_paged(
    db: AsyncSession,
    filters: filters.PlaybookTemplateFilter,
) -> Page[models.PlaybookTemplate]:
    q: Select = select(models.PlaybookTemplate).outerjoin(
        models.PlaybookTemplate.labels
    )
    q = filters.filter(q)  # type: ignore
    try:
        q = filters.sort(q)  # type: ignore
    except NotImplementedError:
        pass
    q = q.group_by(models.PlaybookTemplate.id)
    if filters.search:
        if len(filters.search) == 36:
            q = q.where(
                or_(
                    models.PlaybookTemplate.name.ilike(f"%{filters.search}%"),
                    models.PlaybookTemplate.id == filters.search,
                )
            )
    return await paginate(db, q)


async def get_playbook_template_filters(
    db: AsyncSession, filters: filters.PlaybookTemplateFilter
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []

    q: Select = (
        select(func.count(models.PlaybookTemplate.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )

    q = filters.filter(q)  # type: ignore

    for name in ["tactic", "technique"]:
        entry = await create_filter_for_column(
            db, q, getattr(models.PlaybookTemplate, name), name, name
        )
        result.append(entry)

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


def create_random_color():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return "#{:02x}{:02x}{:02x}".format(int(r), int(g), int(b))


async def create_playbook_template(
    db: AsyncSession, playbook_template: schemas.PlaybookTemplateCreate
) -> models.PlaybookTemplate:
    template = await get_playbook_template(playbook_template.id)
    exists = False
    if not template:
        template = models.PlaybookTemplate(
            id=playbook_template.id,
            name=playbook_template.name,
            icon=playbook_template.icon,
            yaml=playbook_template.yaml,
            tactic=playbook_template.tactic,
            technique=playbook_template.technique,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
    else:
        exists = True
        await db.execute(
            update(models.PlaybookTemplate)
            .where(models.PlaybookTemplate.id == playbook_template.id)
            .values(
                yaml=playbook_template.yaml,
                name=playbook_template.name,
                icon=playbook_template.icon,
                tactic=playbook_template.tactic,
                technique=playbook_template.technique,
            )
        )
        await db.commit()
        template = await db.get(models.PlaybookTemplate, playbook_template.id)
        orm_template_instance = await db.get(models.PlaybookTemplate, playbook_template.id)
        if orm_template_instance:
            template = orm_template_instance

    if exists:
        await delete_label_item(
            db, schemas.LabeledItemDelete(playbook_template_id=template.id)
        )

    for entry in playbook_template.labels or []:
        label = await get_label_by_name(db, entry)
        if not label:
            label = await create_label(
                db,
                schemas.LabelCreate(name=entry, category="Playbooks"),
            )
        await create_label_item(
            db,
            schemas.LabeledItemCreate(
                label_id=label.id,
                playbook_template_id=template.id,
            ),
        )
    return template


async def get_labels_paged(
    db: AsyncSession,
) -> Page[models.Label]:
    return await paginate(
        db, select(models.Label).order_by(models.Label.time_created.desc())
    )


async def get_labels_grouped(
    db: AsyncSession,
) -> list[schemas.LabelView]:
    result_dict: dict[str, schemas.LabelView] = {}
    q = select(models.Label).order_by(models.Label.category)
    result = await db.execute(q)
    for entry in result.scalars().all():
        if entry.category not in result_dict:
            result_dict[entry.category] = schemas.LabelView(
                category=entry.category, labels=[]
            )
        result_dict[entry.category].labels.append(entry)
    return list(result_dict.values())


async def get_labeled_items_list(
    db: AsyncSession,
    host_id: str | None = None,
    c2_implant_id: str | None = None,
    retrieve_parents: bool = False,
) -> List[str]:
    q = select(models.Label.name)
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    filters = []
    if host_id:
        filters.append(models.LabeledItem.host_id == host_id)
        if retrieve_parents:
            filters.append(
                and_(
                    models.Host.id == host_id,
                    models.LabeledItem.domain_id == models.Host.domain_id,
                )
            )
    if c2_implant_id:
        filters.append(models.LabeledItem.c2_implant_id == c2_implant_id)
        if retrieve_parents:
            filters.append(
                and_(
                    models.C2Implant.id == c2_implant_id,
                    models.LabeledItem.host_id == models.C2Implant.host_id,
                )
            )
            filters.append(
                and_(
                    models.C2Implant.id == c2_implant_id,
                    models.C2Implant.host_id == models.Host.id,
                    models.LabeledItem.domain_id == models.Host.domain_id,
                )
            )
    if filters:
        q = q.where(or_(*filters))
    else:
        return []
    result = await db.execute(q)
    return [str(name) for name in result.unique().scalars().all()]


async def create_label(db: AsyncSession, label: schemas.LabelCreate) -> models.Label:
    db_label = models.Label(**label.model_dump())
    db.add(db_label)
    await db.commit()
    await db.refresh(db_label)
    await send_event(schemas.Event.label, schemas.EventType.new, db_label.id)
    return db_label


async def get_label_by_name(db: AsyncSession, name: str) -> Optional[models.Label]:
    q = select(models.Label)
    q = q.where(models.Label.name == name)
    result = await db.execute(q)
    return result.unique().scalar_one_or_none()


async def send_label_events(
    label: schemas.LabeledItemCreate | schemas.LabeledItemDelete,
) -> None:
    dumped_label = label.model_dump(exclude_unset=True)
    dumped_label.pop("label_id", None)

    for key, value in dumped_label.items():
        # Ensure value is not None and key ends with _id (conventional FK name)
        if value is not None and key.endswith("_id"):
            # Derive the object type/cache prefix from the key name
            # e.g., 'host_id' -> 'host', 'c2_implant_id' -> 'c2_implant'
            key_prefix = key.replace("_id", "")

            # --- Added Cache Invalidation Call ---
            logger.info(
                f"Invalidating cache for {key_prefix=}, {value=} due to label change."
            )
            try:
                # Call the standalone invalidation function
                invalidated = await invalidate_cache_entry(
                    key_prefix=key_prefix, key_value=value
                )
                if not invalidated:
                    logger.warning(
                        f"Cache entry for {key_prefix}:{value} may not have existed or Redis error occurred during invalidation."
                    )
            except Exception as e:
                # Catch potential errors from the invalidation function itself
                logger.error(
                    f"Error during cache invalidation call for {key_prefix}:{value}: {e}",
                    exc_info=True,
                )
            # --- End Added Call ---

            # Existing event sending logic
            event = getattr(
                schemas.Event, key_prefix, None
            )  # Use derived prefix for event type
            logger.error(f"Sending event: {event}")
            if event:
                # Assuming send_event is defined and imported correctly
                await send_event(event, schemas.EventType.update, value)
            else:
                logger.warning(
                    f"No matching schemas.Event found for key_prefix '{key_prefix}' derived from '{key}'. Cannot send generic event."
                )

    # for key, value in dumped_label.items():
    #     key = key.replace("_id", "")
    #     event = getattr(schemas.Event, key, None)
    #     if event:
    #         await send_event(event, schemas.EventType.update, value)


async def create_label_item(
    db: AsyncSession, label: schemas.LabeledItemCreate
) -> models.LabeledItem:
    db_label = models.LabeledItem(**label.model_dump())
    db.add(db_label)
    await db.commit()
    await db.refresh(db_label)
    await send_event(schemas.Event.labeled_item, schemas.EventType.new, db_label.id)
    await send_label_events(label)
    return db_label


async def delete_label_item(db: AsyncSession, label: schemas.LabeledItemDelete) -> str:
    q = delete(models.LabeledItem)
    for x, y in label.model_dump().items():
        if y:
            q = q.where(getattr(models.LabeledItem, x) == y)
    await db.execute(q)
    await db.commit()
    await send_event(schemas.Event.labeled_item, schemas.EventType.deleted, "")
    await send_label_events(label)
    return "Success"


async def get_label_categories(
    db: AsyncSession,
) -> Iterable[str]:
    q = select(models.Label.category).group_by(models.Label.category)
    result = await db.execute(q)
    return result.scalars().all()


async def get_c2_servers_paged(db: AsyncSession) -> Page[models.C2Server]:
    return await paginate(
        db, select(models.C2Server).order_by(models.C2Server.time_created.desc())
    )


async def get_c2_servers(db: AsyncSession) -> Iterable[models.C2Server]:
    q = select(models.C2Server)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_c2_implants_paged(
    db: AsyncSession,
    filters: filters.ImplantFilter,
    alive_only: bool = False,
) -> Page[models.C2Implant]:
    q: Select = select(models.C2Implant)
    q = q.outerjoin(models.C2Implant.labels)
    q = filters.filter(q)  # type: ignore
    if alive_only:
        q1 = select(models.LabeledItem.c2_implant_id)
        q1 = q1.where(
            models.LabeledItem.label_id == "d734d03b-50d4-43e3-bb0e-e6bf56ec76b1"
        )
        q = q.where(models.C2Implant.id.not_in(q1))
    try:
        q = filters.sort(q)  # type: ignore
    except NotImplementedError:
        pass
    return await paginate(db, q)


async def get_c2_implant_filters(
    db: AsyncSession,
    filters: filters.ImplantFilter,
    alive_only: bool = False,
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []

    q: Select = (
        select(func.count(models.C2Implant.id).distinct().label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    if alive_only:
        q1 = select(models.LabeledItem.c2_implant_id)
        q1 = q1.where(
            models.LabeledItem.label_id == "d734d03b-50d4-43e3-bb0e-e6bf56ec76b1"
        )
        q = q.where(models.C2Implant.id.not_in(q1))

    for entry in ["os", "payload_type", "c2_type", "username", "domain"]:
        ft_entry = await create_filter_for_column(
            db, q, getattr(models.C2Implant, entry), entry, entry
        )
        result.append(ft_entry)

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    result.append(
        schemas.Filter(
            name="alive_only",
            multiple=False,
            icon="",
            query_name="alive_only",
            type="bool",
        )
    )

    return result


async def get_c2_implants(
    db: AsyncSession,
    c2_server_id: str = "",
    offset: int = 0,
    limit: int = 10,
    not_labels: list[str] | None = None,
    labels: list[str] | None = None,
    last_checkin_before: datetime | None = None,
    last_checkin_after: datetime | None = None,
) -> Iterable[models.C2Implant]:
    q = select(models.C2Implant)
    if c2_server_id:
        q = q.where(models.C2Implant.c2_server_id == c2_server_id)
    if last_checkin_before:
        q = q.where(models.C2Implant.last_checkin <= last_checkin_before)
    if last_checkin_after:
        q = q.where(models.C2Implant.last_checkin >= last_checkin_after)
    if not_labels:
        q1 = select(models.LabeledItem.c2_implant_id)
        q1 = q1.where(models.LabeledItem.label_id == models.Label.id)
        for label in not_labels:
            q1 = q1.where(models.Label.name == label)
        q = q.where(models.C2Implant.id.not_in(q1))

    if labels:
        q1 = select(models.LabeledItem.c2_implant_id)
        q1 = q1.where(models.LabeledItem.label_id == models.Label.id)
        for label in labels:
            q1 = q1.where(models.Label.name == label)
        q = q.where(models.C2Implant.id.in_(q1))

    q = q.offset(offset).limit(limit)
    q = q.order_by(models.C2Implant.time_created.desc())
    result = await db.execute(q)
    return result.scalars().unique().all()


@redis_cache(
    key_prefix="c2_implant",
    session_factory=SessionLocal,
    schema=schemas.C2Implant,  # Ensure this schema exists
    key_param_name="c2_implant_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_c2_implant(
    db: AsyncSession, c2_implant_id: str | uuid.UUID
) -> Optional[models.C2Implant]:
    return await db.get(models.C2Implant, c2_implant_id)


async def get_c2_implant_by_internal_id(
    db: AsyncSession, internal_id: str, c2_server_id: str
) -> Optional[models.C2Implant]:
    q = (
        select(models.C2Implant)
        .where(models.C2Implant.internal_id == internal_id)
        .where(models.C2Implant.c2_server_id == c2_server_id)
        .limit(1)
    )
    result = await db.execute(q)
    return result.unique().scalar_one_or_none()


async def get_c2_tasks_paged(
    db: AsyncSession,
    filters: filters.C2TaskFilter,
) -> Page[models.C2Task]:
    q: Select = (
        select(models.C2Task).outerjoin(models.C2Task.labels).group_by(models.C2Task.id)
    )
    q = filters.filter(q)  # type: ignore
    try:
        q = filters.sort(q)  # type: ignore
    except NotImplementedError:
        pass
    return await paginate(db, q)


async def get_c2_task_filters(
    db: AsyncSession, filters: filters.C2TaskFilter
) -> list[schemas.Filter]:
    q: Select = (
        select(func.count(models.C2Task.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore
    result: list[schemas.Filter] = []

    for column in ["status", "command_name", "operator"]:
        ft_entry = await create_filter_for_column(
            db, q, getattr(models.C2Task, column), column, column
        )
        result.append(ft_entry)

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


async def get_c2_tasks(
    db: AsyncSession,
    filters: filters.C2TaskFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.C2Task]:
    q: Select = (
        select(models.C2Task).outerjoin(models.C2Task.labels).group_by(models.C2Task.id)
    )
    q = filters.filter(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    q = q.order_by(models.C2Task.time_created.desc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_c2_output_paged(
    db: AsyncSession,
    filters: filters.C2OutputFilter,
    c2_job_id: str | None = None,
) -> Page[models.C2Output]:
    q: Select = (
        select(models.C2Output)
        .outerjoin(models.C2Output.labels)
        .group_by(models.C2Output.id)
    )
    q = filters.filter(q)  # type: ignore
    if c2_job_id:
        q = q.where(models.C2Job.id == c2_job_id)
        q = q.where(models.C2Job.c2_task_id == models.C2Output.c2_task_id)
    q = filters.sort(q)  # type: ignore
    return await paginate(db, q)


async def get_c2_output_filters(
    db: AsyncSession,
    filters: filters.C2OutputFilter,
) -> list[schemas.Filter]:
    q: Select = (
        select(func.count(models.C2Output.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore
    result: list[schemas.Filter] = []

    # for column in ['status', 'command_name', 'operator']:
    #     ft_entry = await create_filter_for_column(
    #         db, q, getattr(models.C2Task, column), column, column
    #     )
    #     result.append(ft_entry)

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)
    return result


@redis_cache(
    key_prefix="c2_output",
    session_factory=SessionLocal,
    schema=schemas.C2Output,  # Ensure this schema exists
    key_param_name="c2_output_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_c2_output(
    db: AsyncSession, c2_output_id: str | UUID4
) -> Optional[models.C2Output]:
    return await db.get(models.C2Output, c2_output_id)


async def get_c2_server(
    db: AsyncSession, c2_server_id: str | UUID4
) -> Optional[models.C2Server]:
    return await db.get(models.C2Server, c2_server_id)


async def get_c2_servers_filters(db: AsyncSession, filters: filters.C2ServerFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.C2Server.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in ["type", "name", "hostname", "username"]:
        res = await create_filter_for_column(
            db, q, getattr(models.C2Server, field), field, field
        )
        result.append(res)

    return result


async def update_c2_server(
    db: AsyncSession, c2_server_id: str, c2_server: schemas.C2ServerCreate
) -> models.C2Server | None:
    q = (
        update(models.C2Server)
        .where(models.C2Server.id == c2_server_id)
        .values(**c2_server.model_dump())
    )
    await db.execute(q)
    await db.commit()
    await send_event(schemas.Event.c2_server, schemas.EventType.update, c2_server_id)
    return await db.get(models.C2Server, c2_server_id)


async def create_c2_server(
    db: AsyncSession, c2_server: schemas.C2ServerCreate
) -> models.C2Server | None:
    db_c2_server = models.C2Server(**c2_server.model_dump())
    db.add(db_c2_server)
    await db.commit()
    await db.refresh(db_c2_server)
    await send_event(schemas.Event.c2_server, schemas.EventType.new, db_c2_server.id)
    return db_c2_server


@redis_cache_invalidate(
    key_prefix="c2_implant",
    key_param_name="c2_implant_id",
)
async def update_c2_implant(
    db: AsyncSession, c2_implant_id: str | UUID4, implant: schemas.C2ImplantUpdate
) -> Optional[models.C2Implant]:
    q = update(models.C2Implant).where(models.C2Implant.id == c2_implant_id)
    data = implant.model_dump(
        exclude_none=True, exclude_defaults=True, exclude_unset=True
    )
    # If the dict is empty, performing the query will raise an exception.
    if not data:
        return await db.get(models.C2Implant, c2_implant_id)
    q = q.values(**data)
    await db.execute(q)
    await db.commit()
    await send_event(schemas.Event.c2_implant, schemas.EventType.update, c2_implant_id)
    return await db.get(models.C2Implant, c2_implant_id)


async def create_or_update_c2_implant(
    db: AsyncSession, implant: schemas.C2ImplantCreate
) -> Tuple[bool, models.C2Implant]:
    """Creates the implant in the database, if the implant with that id already exists, updates it.
    returns tuple[bool, C2Implant]
    The bool indicates if the implant was creaed.
    """
    q = select(models.C2Implant).where(
        models.C2Implant.c2_server_id == implant.c2_server_id
    )
    if implant.internal_id:
        q = q.where(models.C2Implant.internal_id == implant.internal_id)
    res = await db.execute(q)
    db_implant = res.scalars().first()
    if db_implant:
        q = (
            update(models.C2Implant)
            .where(models.C2Implant.id == db_implant.id)
            .values(
                **implant.model_dump(
                    exclude_none=True, exclude_unset=True, exclude_defaults=True
                )
            )
        )
        await db.execute(q)
        await db.commit()
        await invalidate_cache_entry("c2_implant", db_implant.id)
        await send_event(
            schemas.Event.c2_implant, schemas.EventType.update, db_implant.id
        )
        new = False
    else:
        db_implant = models.C2Implant(**implant.model_dump())
        db.add(db_implant)
        await db.commit()
        await db.refresh(db_implant)
        await send_event(schemas.Event.c2_implant, schemas.EventType.new, db_implant.id)
        new = True

    return new, db_implant


async def create_or_update_c2_task(
    db: AsyncSession, task: schemas.C2TaskCreate
) -> Tuple[bool, models.C2Task]:
    """Creates the c2 task in the database, if the c2 task with that id already exists, updates it.
    returns tuple[bool, C2Task]
    The bool indicates if the task was created.
    """
    q = (
        select(models.C2Task)
        .where(models.C2Task.c2_server_id == task.c2_server_id)
        .where(models.C2Task.internal_id == task.internal_id)
    )
    res = await db.execute(q)
    db_task = res.scalars().first()
    data = task.model_dump()
    data.pop("internal_implant_id", None)
    if db_task:
        new = False
        q = update(models.C2Task).where(models.C2Task.id == db_task.id)
        q = q.values(**data)
        await db.execute(q)
        await db.commit()
        await invalidate_cache_entry("c2_task", db_task.id)
        await send_event(schemas.Event.c2_task, schemas.EventType.update, db_task.id)
    else:
        db_task = models.C2Task(**data)
        db.add(db_task)
        await db.commit()
        await db.refresh(db_task)
        await send_event(schemas.Event.c2_task, schemas.EventType.new, db_task.id)
        new = True
    return new, db_task


async def create_c2_task_output(
    db: AsyncSession, c2_outputs: schemas.C2OutputCreate
) -> Tuple[bool, models.C2Output]:
    data = c2_outputs.model_dump()
    data.pop("internal_task_id", None)
    data.pop("processes", [])
    data.pop("files", [])
    data.pop("bucket", "")
    data.pop("path", "")
    data.pop("file_list", "")

    q = insert(models.C2Output).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update("c2_output_uc", set_=data)
    result = await db.scalars(
        update_stmt.returning(models.C2Output),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    if result.time_updated == None:
        await send_event(schemas.Event.c2_task_output, schemas.EventType.new, result.id)
    return result.time_updated == None, result


@redis_cache(
    key_prefix="c2_task",
    session_factory=SessionLocal,
    schema=schemas.C2Task,  # Ensure this schema exists
    key_param_name="c2_task_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_c2_task(db, c2_task_id: str | UUID4) -> Optional[models.C2Task]:
    return await db.get(models.C2Task, c2_task_id)


async def get_c2_task_by_internal_id(
    db, internal_id: str, c2_server_id: str | UUID4
) -> Optional[models.C2Task]:
    q = (
        select(models.C2Task)
        .where(models.C2Task.internal_id == internal_id)
        .where(models.C2Task.c2_server_id == c2_server_id)
        .limit(1)
    )
    result = await db.execute(q)
    return result.unique().scalar_one_or_none()


async def get_c2_task_output(
    db,
    filters: filters.C2OutputFilter,
    c2_job_id: str | UUID4 = "",
) -> Iterable[models.C2Output]:
    q: Select = (
        select(models.C2Output)
        .outerjoin(models.C2Output.labels)
        .group_by(models.C2Output.id)
    )
    q = filters.filter(q)  # type: ignore
    if c2_job_id:
        q = q.where(models.C2Job.id == c2_job_id)
        q = q.where(models.C2Job.c2_task_id == models.C2Output.c2_task_id)
    q = filters.sort(q)  # type: ignore
    result = await db.execute(q)
    return result.scalars().unique().all()


async def update_c2_task_summary(
    db, c2_task_id: str | UUID4, summary: str, status: str
) -> None:
    q = (
        update(models.C2Task)
        .where(models.C2Task.id == c2_task_id)
        .values(processing_status=status, ai_summary=summary)
    )
    await db.execute(q)
    await db.commit()
    await invalidate_cache_entry("c2_task", c2_task_id)
    await send_event(schemas.Event.c2_task, schemas.EventType.update, c2_task_id)


async def get_timeline_paged(
    db: AsyncSession,
    filters: filters.TimeLineFilter,
) -> Page[Union[models.C2Task, models.ProxyJob, models.ManualTimelineTask]]:
    q: Select = select(models.TimeLine)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    return await paginate(db, q)


async def get_timeline_filters(db: AsyncSession, filters: filters.TimeLineFilter):
    result: list[schemas.Filter] = []
    q: Select = select(func.count(models.TimeLine.id.distinct()).label("count_1"))
    q = filters.filter(q)  # type: ignore
    for field in ["status"]:
        res = await create_filter_for_column(
            db, q, getattr(models.TimeLine, field), field, field
        )
        result.append(res)
    return result


async def get_timeline(
    db: AsyncSession, status: list[str]
) -> Iterable[Union[models.C2Task, models.ProxyJob]]:
    q = select(models.TimeLine).options(joinedload("*"))

    if status:
        q = q.where(models.TimeLine.status.in_(status))

    q = q.order_by(models.TimeLine.time_completed.asc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def list_situational_awareness(
    db,
    name: str = "",
    category: str = "",
    domain_id: str | UUID4 = "",
    limit: int = 10,
    offset: int = 0,
) -> Iterable[models.SituationalAwareness]:
    q = select(models.SituationalAwareness)
    if name:
        q = q.where(models.SituationalAwareness.name == name)
    if category:
        q = q.where(models.SituationalAwareness.category == category)
    if domain_id:
        q = q.where(models.SituationalAwareness.domain_id == domain_id)
    q = q.limit(limit).offset(offset)
    q = q.order_by(models.SituationalAwareness.time_created.desc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def list_situational_awarenesss_paged(
    db: AsyncSession, filters: filters.SituationalAwarenessFilter
) -> Page[models.SituationalAwareness]:
    q: Select = select(models.SituationalAwareness)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.SituationalAwareness.id)
    return await paginate(db, q)


async def get_situational_awarenesss_filters(
    db: AsyncSession, filters: filters.SituationalAwarenessFilter
):
    result: list[schemas.Filter] = []
    q: Select = select(
        func.count(models.SituationalAwareness.id.distinct()).label("count_1")
    )
    q = filters.filter(q)  # type: ignore

    for field in ["name", "category"]:
        res = await create_filter_for_column(
            db, q, getattr(models.SituationalAwareness, field), field, field
        )
        result.append(res)

    return result


# --- SituationalAwareness ---
@redis_cache(
    key_prefix="situational_awareness",
    session_factory=SessionLocal,
    schema=schemas.SituationalAwareness,  # Ensure this schema exists
    key_param_name="sa_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_situational_awareness(
    db, sa_id: str | UUID4
) -> Optional[models.SituationalAwareness]:
    return await db.get(models.SituationalAwareness, sa_id)


async def update_situational_awareness(
    db, sa_id: str | UUID4, sa: schemas.SituationalAwarenessCreate
):
    q = (
        update(models.SituationalAwareness)
        .where(models.SituationalAwareness.id == sa_id)
        .values(**sa.model_dump())
    )
    await db.execute(q)
    await db.commit()
    await send_event(
        schemas.Event.situational_awareness, schemas.EventType.update, sa_id
    )


async def delete_situational_awareness(db, sa_id: str | UUID4):
    q = q = delete(models.SituationalAwareness).where(
        models.SituationalAwareness.id == sa_id
    )
    await db.execute(q)
    await db.commit()
    await send_event(
        schemas.Event.situational_awareness, schemas.EventType.deleted, sa_id
    )


async def get_or_create_situational_awareness(
    db, sa: schemas.SituationalAwarenessCreate
) -> Tuple[bool, models.SituationalAwareness]:
    created = False
    q = (
        select(models.SituationalAwareness)
        .where(models.SituationalAwareness.name == sa.name)
        .where(models.SituationalAwareness.category == sa.category)
    )
    if sa.value_string != None:
        q = q.where(models.SituationalAwareness.value_string == sa.value_string)
    if sa.value_bool != None:
        q = q.where(models.SituationalAwareness.value_bool == sa.value_bool)
    if sa.value_int != None:
        q = q.where(models.SituationalAwareness.value_int == sa.value_int)
    if sa.value_json != None:
        q = q.where(models.SituationalAwareness.value_json == sa.value_json)
    q = await db.execute(q)
    sa_db = q.scalars().unique().first()
    if not sa_db:
        created = True
        sa_db = models.SituationalAwareness(**sa.model_dump())
        db.add(sa_db)
        await db.commit()
        await db.refresh(sa_db)
        await send_event(
            schemas.Event.situational_awareness, schemas.EventType.new, sa_db.id
        )
    return created, sa_db


@redis_cache_fixed_key(
    cache_key="sa_statistics",
    session_factory=SessionLocal,  # Use your SessionLocal
    schema=schemas.StatisticsItems,
)
async def get_sa_statistics(db: AsyncSession) -> dict:
    stats = {}
    q = select(
        models.SituationalAwareness.category, func.count(models.SituationalAwareness.id)
    ).group_by(models.SituationalAwareness.category)
    result = await db.execute(q)
    for entry in result.all():
        if entry[0]:
            stats[entry[0]] = entry[1]
    return dict(items=[dict(key=key, value=value) for key, value in stats.items()])


async def get_or_create_share(
    db: AsyncSession, share: schemas.ShareCreate
) -> Tuple[bool, models.Share]:
    s = (
        select(models.Share)
        .where(models.Share.name == share.name)
        .where(models.Share.host_id == share.host_id)
    )
    q = await db.execute(s)
    db_share = q.scalars().first()
    if not db_share:
        db_share = models.Share(**share.model_dump())
        db.add(db_share)
        try:
            await db.commit()
            await db.refresh(db_share)
            await send_event(schemas.Event.share, schemas.EventType.new, db_share.id)
            if share.name and (
                "$" in share.name
                or share.name.lower()
                in [
                    "sysvol",
                    "wsuscontent",
                    "wsustemp",
                    "updateservicespackages",
                ]
            ):
                await create_label_item(
                    db,
                    label=schemas.LabeledItemCreate(
                        label_id="3f061979-055d-473f-ba15-d7b508f0ba83",
                        share_id=db_share.id,
                    ),
                )
            return True, db_share
        except exc.IntegrityError:
            await db.rollback()
            return await get_or_create_share(db, share)
    return False, db_share


async def list_shares_paged(
    db,
    share_filters: filters.ShareFilter,
) -> Page[models.Share]:
    q: Select = (
        select(models.Share).outerjoin(models.Share.labels).group_by(models.Share.id)
    )
    q = share_filters.filter(q)  # type: ignore
    return await paginate(db, q)


async def get_shares(
    db: AsyncSession,
    filters: filters.ShareFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Share]:
    q: Select = select(models.Share)
    q = q.outerjoin(models.Share.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_share_filters(
    db: AsyncSession,
    share_filters: filters.ShareFilter,
) -> list[schemas.Filter]:
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Share.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = share_filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    return result


@redis_cache(
    key_prefix="share",
    session_factory=SessionLocal,
    schema=schemas.Share,  # Ensure this schema exists
    key_param_name="share_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_share(db: AsyncSession, share_id: str | UUID4) -> Optional[models.Share]:
    return await db.get(models.Share, share_id)


async def create_share_file(
    db: AsyncSession, share_file: schemas.ShareFileCreate
) -> models.ShareFile:
    # Indexed is potentially set to false here
    q = insert(models.ShareFile).values(**share_file.model_dump())
    # Only overwrite indexed in the current data if its set to True.
    data = share_file.model_dump()
    indexed = data.pop("indexed")
    if indexed:
        data["indexed"] = True
    update_stmt = q.on_conflict_do_update("share_files_unc_path", set_=data)
    # await session.execute(update_stmt)
    result = await db.scalars(
        update_stmt.returning(models.ShareFile),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    return result.unique().one()


async def set_share_file_downloaded(
    db: AsyncSession, share_file_id: str | UUID4
) -> None:
    await db.execute(
        update(models.ShareFile)
        .where(models.ShareFile.id == share_file_id)
        .values(downloaded=True)
    )
    await db.commit()
    await invalidate_cache_entry("share_file", share_file_id)
    await send_event(schemas.Event.share_file, schemas.EventType.update, share_file_id)


async def list_share_files_paged(
    db: AsyncSession,
    share_id: str | UUID4 | None = None,
    depth: int = -1,
    parent_id: str | UUID4 | None = None,
    search: str = "",
    labels_only: bool = False,
) -> Page[models.ShareFile]:
    q = select(models.ShareFile)
    if share_id:
        q = q.where(models.ShareFile.share_id == share_id)
    if depth > -1:
        q = q.where(models.ShareFile.depth == depth)
    if parent_id:
        q = q.where(models.ShareFile.parent_id == parent_id)
    if search:
        q = q.where(models.ShareFile.unc_path.ilike(f"%{search}%"))
    if labels_only:
        q = q.where(models.LabeledItem.share_file_id == models.ShareFile.id)
    q = q.order_by(models.ShareFile.name.asc())
    return await paginate(db, q)


async def list_share_files(
    db: AsyncSession,
    share_id: str | UUID4 | None = None,
    depth: int = -1,
    parent_id: str | UUID4 | None = None,
    search: str = "",
    labels_only: bool = False,
    type: str = "",
    indexed: bool | None = None,
    downloaded: bool | None = None,
    max_size: int = 0,
    limit: int = 0,
) -> Iterable[models.ShareFile]:
    q = select(models.ShareFile)
    if share_id:
        q = q.where(models.ShareFile.share_id == share_id)
    if depth > -1:
        q = q.where(models.ShareFile.depth == depth)
    if parent_id:
        q = q.where(models.ShareFile.parent_id == parent_id)
    if search:
        q = q.where(models.ShareFile.unc_path.ilike(f"%{search}%"))
    if labels_only:
        q = q.where(models.LabeledItem.share_file_id == models.ShareFile.id)
    if indexed is not None:
        q = q.where(models.ShareFile.indexed == indexed)
    if type:
        q = q.where(models.ShareFile.type == type)
    if downloaded is not None:
        q = q.where(models.ShareFile.downloaded == downloaded)
    if max_size:
        q = q.where(models.ShareFile.size < max_size)

    q = q.order_by(models.ShareFile.name.asc())
    if limit:
        q = q.limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_share_files_paged(
    db: AsyncSession, filters: filters.ShareFileFilter
) -> Page[models.ShareFile]:
    q: Select = select(models.ShareFile)
    q = q.outerjoin(models.ShareFile.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.ShareFile.id)
    return await paginate(db, q)


async def get_share_files(
    db: AsyncSession,
    filters: filters.ShareFileFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.ShareFile]:
    q: Select = select(models.ShareFile)
    q = q.outerjoin(models.ShareFile.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_share_file_filters(db: AsyncSession, filters: filters.ShareFileFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.ShareFile.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in ["type", "downloaded", "indexed", "depth", "extension"]:
        res = await create_filter_for_column(
            db, q, getattr(models.ShareFile, field), field, field
        )
        result.append(res)

    return result


@redis_cache(
    key_prefix="share_file",
    session_factory=SessionLocal,
    schema=schemas.ShareFile,  # Ensure this schema exists
    key_param_name="id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_share_file(
    db: AsyncSession, id: UUID4 | str
) -> Optional[models.ShareFile]:
    return await db.get(models.ShareFile, id)


async def save_parsed_share_file(
    db: AsyncSession, file: schemas.BaseParsedShareFile
) -> Tuple[models.Share, models.ShareFile]:
    domain_id = None
    host_id = None
    if file.domain:
        d = await get_or_create_domain(db, file.domain)
        domain_id = d.id

    _, h = await get_or_create_host(db, file.hostname, domain_id)
    host_id = h.id

    _, share_db = await get_or_create_share(
        db,
        schemas.ShareCreate(
            host_id=host_id, name=file.sharename, unc_path=file.share_unc_path
        ),
    )

    parent_id = None
    for parent in file.parents:
        parent_share_file = schemas.ShareFileCreate(
            type=parent.type,
            parent_id=parent_id,
            size=parent.size,
            share_id=share_db.id,
            indexed=parent.indexed,
            depth=parent.depth,
            name=parent.name,
            unc_path=parent.unc_path,
        )
        parent_db = await create_share_file(db, parent_share_file)
        parent_id = parent_db.id

    share_file = schemas.ShareFileCreate(
        type=file.type,
        parent_id=parent_id,
        share_id=share_db.id,
        size=file.size,
        last_modified=file.timestamp,  # type: ignore
        unc_path=file.unc_path,
        name=file.name,
        depth=file.depth,
        indexed=True,
    )

    parent_id = None
    if file.depth == 0:
        await create_label_item(
            db,
            schemas.LabeledItemCreate(
                label_id="851853d0-e540-4185-b46e-cf2e0cc63aa8",
                share_id=share_db.id,
            ),
        )
    else:
        share_file = await create_share_file(db, share_file)
        parent_id = share_file.id
        await db.commit()

    if file.children:
        await save_objects(
            db,
            entries=file.children,
            parent_name=file.unc_path,
            share_id=share_db.id,
            depth=file.depth,
            parent_id=parent_id,
        )

    await db.commit()
    return share_db, share_file


async def save_objects(
    db: AsyncSession,
    entries: list[schemas.BaseParsedShareFile],
    parent_name: str,
    share_id: str | uuid.UUID,
    depth: int,
    parent_id: str | uuid.UUID | None,
) -> None:
    for entry in entries:
        unc_file_path = ntpath.join(parent_name, entry.name)
        file = schemas.ShareFileCreate(
            type=entry.type,
            share_id=share_id,
            size=entry.size,
            last_modified=entry.timestamp,  # type: ignore
            unc_path=unc_file_path,
            name=entry.name,
            depth=depth + 1,
            parent_id=parent_id,
            indexed=len(entry.children) > 0 and entry.type == "dir",
        )
        file_db = await create_share_file(db, file)
        await db.commit()
        await save_objects(
            db, entry.children, unc_file_path, share_id, depth + 1, file_db.id
        )


@redis_cache_fixed_key(
    cache_key="share_statistics",
    session_factory=SessionLocal,  # Use your SessionLocal
    schema=schemas.StatisticsItems,
)
async def get_share_statistics(db: AsyncSession) -> dict:
    stats = {}
    q = select(func.count(models.Share.id))
    result = await db.execute(q)
    entry = result.scalars().first()
    stats["Shares"] = entry

    q = select(func.count(models.ShareFile.id))
    result = await db.execute(q)
    entry = result.scalars().first()
    stats["Files"] = entry

    q = select(func.count(models.Highlight.id))
    result = await db.execute(q)
    entry = result.scalars().first()
    stats["Highlights"] = entry

    return dict(items=[dict(key=key, value=value) for key, value in stats.items()])


async def get_domain_name_from_host(db: AsyncSession, host_id: str | UUID4) -> str:
    q = (
        select(models.Domain)
        .where(models.Host.domain_id == models.Domain.id)
        .where(models.Host.id == host_id)
    )
    result = await db.execute(q)
    domain_db = result.scalars().first()
    if domain_db:
        if domain_db.long_name:
            return domain_db.long_name
        elif domain_db.short_name:
            return domain_db.short_name
    return ""


async def update_c2_server_status(
    db: AsyncSession, c2_server_id: str | UUID4, status: schemas.C2ServerStatus
):
    q = (
        select(models.C2ServerStatus)
        .where(models.C2ServerStatus.c2_server_id == c2_server_id)
        .where(models.C2ServerStatus.name == status.name)
    )
    res = await db.execute(q)
    status_db = res.scalars().unique().first()
    if status_db:
        q = (
            update(models.C2ServerStatus)
            .where(models.C2ServerStatus.id == status_db.id)
            .values(**status.model_dump())
        )
        await db.execute(q)
        await db.commit()
    else:
        status_db = models.C2ServerStatus(
            **status.model_dump(), c2_server_id=c2_server_id
        )
        db.add(status_db)
        await db.commit()


async def list_c2_server_status(db: AsyncSession) -> Iterable[models.C2ServerStatus]:
    q = select(models.C2ServerStatus)
    result = await db.execute(q)
    return result.scalars().all()


async def delete_c2_server_status(db: AsyncSession, status_id: UUID4 | str) -> None:
    q = delete(models.C2ServerStatus).where(models.C2ServerStatus.id == status_id)
    await db.execute(q)
    await db.commit()


async def delete_c2_server_status_custom(
    db: AsyncSession, c2_server_id: str | UUID4, status: schemas.C2ServerStatus
) -> None:
    q = (
        delete(models.C2ServerStatus)
        .where(models.C2ServerStatus.c2_server_id == c2_server_id)
        .where(models.C2ServerStatus.name == status.name)
    )
    await db.execute(q)
    await db.commit()


@redis_cache_fixed_key(
    cache_key="c2_server_statistics",
    session_factory=SessionLocal,  # Use your SessionLocal
    schema=schemas.StatisticsItems,
)
async def get_c2_server_statistics(db: AsyncSession) -> dict:
    stats = {}
    c2_server_stats = {}
    icon_map = {
        "Container: running": "check",
        "Container: exited": "close",
        "Container: stopping": "close",
        "Container: restarting": "hourglass",
        "Container: restarted": "hourglass",
        "Container: deleting": "delete",
        "Socks: linux docker": "check",
        "Socks: windows docker": "check",
    }

    q = select(models.C2Server)
    result = await db.execute(q)
    for entry in result.scalars().unique().all():
        q2 = select(models.C2ServerStatus).where(
            models.C2ServerStatus.c2_server_id == entry.id
        )
        result2 = await db.execute(q2)
        found = False
        for status in result2.scalars().unique().all():
            found = True
            if f"Container: {status.status}" not in stats:
                stats[f"Container: {status.status}"] = 0
            stats[f"Container: {status.status}"] += 1
        if not found:
            if "Container: missing" not in stats:
                stats["Container: missing"] = 0
            stats["Container: missing"] += 1
        if entry.type not in c2_server_stats:
            c2_server_stats[entry.type] = 0
        c2_server_stats[entry.type] += 1
    c2_server_stats.update(stats)

    q = select(models.SocksServer)
    result = await db.execute(q)
    for entry in result.scalars().unique().all():
        name = f"Socks: {entry.operating_system} {entry.type}"
        if name not in c2_server_stats:
            c2_server_stats[name] = 0
        c2_server_stats[name] += 1

    return dict(
        items=[
            dict(key=key, value=value, icon=icon_map.get(key, "question_mark"))
            for key, value in c2_server_stats.items()
        ]
    )


async def create_hash(
    db: AsyncSession, hash: schemas.HashCreate
) -> Tuple[bool, models.Hash]:
    q = select(models.Hash).where(models.Hash.hash == hash.hash)
    result = await db.execute(q)
    hash_db = result.scalars().first()
    if hash_db:
        return False, hash_db
    else:
        hash_db = models.Hash(**hash.model_dump())
        db.add(hash_db)
        await db.commit()
        await db.refresh(hash_db)
        await send_event(schemas.Event.hash, schemas.EventType.new, hash_db.id)
        return True, hash_db


@redis_cache(
    key_prefix="hash",
    session_factory=SessionLocal,
    schema=schemas.Hash,  # Ensure this schema exists
    key_param_name="hash_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_hash(db: AsyncSession, hash_id: UUID4 | str) -> Optional[models.Hash]:
    return await db.get(models.Hash, hash_id)


async def list_hashes_paged(db: AsyncSession) -> Page[models.Hash]:
    q = select(models.Hash)
    return await paginate(db, q)


async def list_hashes(db: AsyncSession) -> Iterable[models.Hash]:
    q = select(models.Hash).order_by(models.Hash.time_created.desc())
    result = await db.execute(q)
    return result.scalars().unique().all()


async def delete_hash(db: AsyncSession, hash_id: UUID4 | str) -> None:
    q = delete(models.Hash).where(models.Hash.id == hash_id)
    await db.execute(q)


async def update_c2_job_c2_task_id(
    db: AsyncSession, c2_job_id: UUID4 | str, c2_task_id: UUID4 | str
) -> None:
    q = (
        update(models.C2Job)
        .where(models.C2Job.id == c2_job_id)
        .values(c2_task_id=c2_task_id)
    )
    await db.execute(q)
    await db.commit()


async def indexer_list_shares(
    db: AsyncSession, max_shares: int = 0, not_label_ids: list[str] | None = None
) -> Iterable[models.Share]:
    """
    List shares
    """
    q = select(models.Share)

    q = q.filter(~models.Share.id.in_(select(models.ShareFile.share_id).distinct()))
    if max_shares > 0:
        q = q.limit(max_shares)

    if not_label_ids:
        q1 = select(models.LabeledItem.share_id)
        q1 = q1.where(models.LabeledItem.label_id.in_(not_label_ids))
        q = q.where(models.Share.id.not_in(q1))

    dq = await db.execute(q)
    return dq.scalars().unique().all()


async def indexer_list_shares_filtered(
    db: AsyncSession,
    max_shares: int = 0,
    not_label_ids: list[str] | None = None,
    depth: int = -1,
    file_type: str = "",
    indexed: bool | None = None,
    search: str = "",
) -> Iterable[str]:
    q = select(models.Share.id)

    if not_label_ids:
        q1 = select(models.LabeledItem.share_id)
        q1 = q1.where(models.LabeledItem.label_id.in_(not_label_ids))
        q = q.where(models.Share.id.not_in(q1))

    q2 = select(models.ShareFile.share_id).where(models.ShareFile.share_id.in_(q))

    if depth > -1:
        q2 = q2.filter(models.ShareFile.depth == depth)

    if file_type:
        q2 = q2.filter(models.ShareFile.type == file_type)

    if indexed is not None:
        q2 = q2.filter(models.ShareFile.indexed == indexed)

    if max_shares > 0:
        q2 = q2.limit(max_shares)

    if search:
        q2 = q2.filter(models.ShareFile.like(f"%{search}%"))

    dq = await db.execute(q2)
    return dq.scalars().unique().all()


async def get_playbook_steps_modifiers_paged(
    db: AsyncSession, playbook_step_id: UUID4 | str
) -> Page[models.PlaybookStepModifier]:
    q = select(models.PlaybookStepModifier).order_by(
        models.PlaybookStepModifier.time_created.desc()
    )
    if playbook_step_id:
        q = q.where(models.PlaybookStepModifier.playbook_step_id == playbook_step_id)
    return await paginate(db, q)


async def get_playbook_steps_modifiers(
    db: AsyncSession, playbook_step_id: UUID4 | str
) -> Iterable[models.PlaybookStepModifier]:
    q = select(models.PlaybookStepModifier).order_by(
        models.PlaybookStepModifier.time_created.desc()
    )
    if playbook_step_id:
        q = q.where(models.PlaybookStepModifier.playbook_step_id == playbook_step_id)
    resp = await db.execute(q)
    return resp.scalars().unique().all()


async def create_playbook_step_modifier(
    db: AsyncSession, step: schemas.PlaybookStepModifierCreate
) -> models.PlaybookStepModifier:
    db_step = models.PlaybookStepModifier(**step.model_dump())
    db.add(db_step)
    await db.commit()
    await db.refresh(db_step)
    # TODO
    # if step.playbook_id:
    #     msg = messages_pb2.Event(event="new_step", id=str(step.id))
    #     await redis.publish(f"playbook_stream_{step.playbook_id}", msg.SerializeToString())
    # await send_event(schemas.Event.domain, schemas.EventType.new, db_domain.id)
    return db_step


async def get_playbook_step_modifier(
    db: AsyncSession, step_id: str | UUID4
) -> models.PlaybookStepModifier | None:
    return await db.get(models.PlaybookStepModifier, step_id)


async def update_playbook_step_modifier(
    db: AsyncSession, step_id: str, step: schemas.PlaybookStepModifierCreate
) -> Optional[models.PlaybookStepModifier]:
    step_db = await get_playbook_step_modifier(db, step_id=step_id)
    if step_db:
        q = (
            update(models.PlaybookStepModifier)
            .where(models.PlaybookStepModifier.id == step_id)
            .values(**step.model_dump())
        )
        await db.execute(q)
        await db.commit()
        await db.refresh(step_db)
        return step_db
    return None


async def delete_playbook_step_modifier(db: AsyncSession, step_id: str | UUID4) -> None:
    step_db = await get_playbook_step_modifier(db, step_id=step_id)
    if step_db:
        await db.execute(
            delete(models.PlaybookStepModifier).where(
                models.PlaybookStepModifier.id == step_id
            )
        )
        await db.commit()


async def recurse_labels_c2_implant(
    db: AsyncSession, c2_implant_id: str | UUID4
) -> Iterable[schemas.Label]:
    q = select(models.Label)
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.c2_implant_id == c2_implant_id)
    resp = await db.execute(q)
    result = [schemas.Label.model_validate(l) for l in resp.scalars().unique().all()]

    # host
    q = select(models.Label)
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.host_id == models.C2Implant.host_id)
    q = q.where(models.C2Implant.id == c2_implant_id)

    resp = await db.execute(q)
    result.extend(
        [schemas.Label.model_validate(l) for l in resp.scalars().unique().all()]
    )

    # domain
    q = select(models.Label)
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.domain_id == models.Host.domain_id)
    q = q.where(models.C2Implant.host_id == models.Host.id)
    q = q.where(models.C2Implant.id == c2_implant_id)
    resp = await db.execute(q)
    result.extend(
        [schemas.Label.model_validate(l) for l in resp.scalars().unique().all()]
    )
    return result


async def recurse_labels(db: AsyncSession, timeline_id: str | UUID4) -> Iterable[str]:
    q = select(func.distinct(models.Label.name))
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(
        or_(
            models.LabeledItem.c2_task_id == timeline_id,
            models.LabeledItem.proxy_job_id == timeline_id,
        )
    )
    resp = await db.execute(q)
    result = list(resp.scalars().unique().all())

    # for c2_tasks check implant
    q = select(func.distinct(models.Label.name))
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.c2_implant_id == models.C2Task.c2_implant_id)
    q = q.where(models.C2Task.id == timeline_id)
    resp = await db.execute(q)
    result.extend(list(resp.scalars().unique().all()))

    # host
    q = select(func.distinct(models.Label.name))
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.host_id == models.C2Implant.host_id)
    q = q.where(models.C2Implant.id == models.C2Task.c2_implant_id)
    q = q.where(models.C2Task.id == timeline_id)

    resp = await db.execute(q)
    result.extend(list(resp.scalars().unique().all()))

    # domain
    q = select(func.distinct(models.Label.name))
    q = q.where(models.LabeledItem.label_id == models.Label.id)
    q = q.where(models.LabeledItem.domain_id == models.Host.domain_id)
    q = q.where(models.C2Implant.host_id == models.Host.id)
    q = q.where(models.C2Implant.id == models.C2Task.c2_implant_id)
    q = q.where(models.C2Task.id == timeline_id)

    resp = await db.execute(q)
    result.extend(list(resp.scalars().unique().all()))

    return result


async def create_parse_result(
    db: AsyncSession, result: schemas.ParseResultCreate
) -> models.ParseResult:
    result_db = models.ParseResult(**result.model_dump())
    db.add(result_db)
    await db.commit()
    await db.refresh(result_db)
    # await send_event(schemas.Event.domain, schemas.EventType.new, db_domain.id)
    return result_db


@redis_cache(
    key_prefix="parse_result",
    session_factory=SessionLocal,
    schema=schemas.ParseResult,  # Ensure this schema exists
    key_param_name="result_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_parse_result(
    db: AsyncSession, result_id: UUID4 | str
) -> Optional[models.ParseResult]:
    return await db.get(models.ParseResult, result_id)


async def get_parse_results_paged(
    db: AsyncSession,
    file_id: str | UUID4 | None = None,
    c2_task_id: str | UUID4 | None = None,
    c2_task_output_id: str | UUID4 | None = None,
    proxy_job_output_id: str | UUID4 | None = None,
    proxy_job_id: str | UUID4 | None = None,
) -> Page[models.ParseResult]:
    q = select(models.ParseResult)

    if file_id:
        q = q.where(models.ParseResult.file_id == file_id)
    if c2_task_id:
        q = q.where(models.ParseResult.c2_task_id == c2_task_id)
    if c2_task_output_id:
        q = q.where(models.ParseResult.c2_task_output_id == c2_task_output_id)
    if proxy_job_output_id:
        q = q.where(models.ParseResult.proxy_job_output_id == proxy_job_output_id)
    if proxy_job_id:
        q = q.where(models.ParseResult.proxy_job_id == proxy_job_id)

    q = q.order_by(models.ParseResult.time_created.asc())
    return await paginate(
        db,
        q,
    )


async def create_highlight(
    db: AsyncSession, highlight: schemas.HighlightCreate
) -> models.Highlight:
    result = models.Highlight(**highlight.model_dump())
    db.add(result)
    await db.commit()
    await db.refresh(result)
    await send_event(schemas.Event.highlight, schemas.EventType.new, result.id)
    return result


@redis_cache(
    key_prefix="highlight",
    session_factory=SessionLocal,
    schema=schemas.Highlight,  # Ensure this schema exists
    key_param_name="highlight_id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_highlight(
    db: AsyncSession, highlight_id: UUID4 | str
) -> Optional[models.Highlight]:
    return await db.get(models.Highlight, highlight_id)


async def get_highlights_paged(
    db: AsyncSession, filters: filters.HighlightFilter
) -> Page[models.Highlight]:
    q: Select = select(models.Highlight)
    q = q.outerjoin(models.Highlight.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.Highlight.id)
    return await paginate(db, q)


async def get_highlights_filters(db: AsyncSession, filters: filters.HighlightFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Highlight.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in ["rule_type", "hit"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Highlight, field), field, field
        )
        result.append(res)

    return result


async def create_setting(db: AsyncSession, setting: schemas.SettingCreate):
    q = insert(models.Setting).values(**setting.model_dump())
    update_stmt = q.on_conflict_do_nothing("name_category")
    await db.execute(update_stmt)
    await db.scalars(
        update_stmt.returning(models.Setting),
        execution_options={"populate_existing": True},
    )
    await db.commit()


async def get_settings(db: AsyncSession) -> list[schemas.Settings]:
    result: list[schemas.Settings] = []
    q = select(models.SettingCategory).order_by(models.SettingCategory.order)
    res = await db.execute(q)
    for entry in res.scalars().all():
        q2 = (
            select(models.Setting)
            .where(models.Setting.category_id == entry.id)
            .order_by(models.Setting.name)
        )
        res2 = await db.execute(q2)
        result.append(
            schemas.Settings(
                name=entry.name,
                icon=entry.icon,
                description=entry.description,
                order=entry.order,
                settings=list(res2.scalars().all()),
            )
        )
    return result


async def create_setting_category(
    db: AsyncSession, category: schemas.SettingCategoryCreate
) -> models.SettingCategory:
    data = category.model_dump()
    settings = data.pop("settings")
    q = insert(models.SettingCategory).values(**data)
    update_stmt = q.on_conflict_do_update(
        "setting_category_name_key",
        set_=dict(
            description=category.description, icon=category.icon, order=category.order
        ),
    )
    result = await db.scalars(
        update_stmt.returning(models.SettingCategory),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    return result.unique().one()


async def update_setting(
    db: AsyncSession, setting_id: UUID4, setting: schemas.SettingModify
) -> None:
    q = (
        update(models.Setting)
        .where(models.Setting.id == setting_id)
        .values(value=setting.value)
    )
    await db.execute(q)
    await db.commit()


async def get_setting(
    db: AsyncSession, category_name: str, setting_name: str, default: Any
) -> Any | None:
    q = (
        select(models.Setting.value)
        .where(models.Setting.category_id == models.SettingCategory.id)
        .where(models.SettingCategory.name == category_name)
        .where(models.Setting.name == setting_name)
    )

    resp = await db.execute(q)
    result = resp.scalar_one_or_none()
    if result:
        return result
    else:
        return default


async def create_socks_server(
    db: AsyncSession, socks_server: schemas.SocksServerCreate
) -> models.SocksServer:
    q = insert(models.SocksServer).values(**socks_server.model_dump())
    q = q.on_conflict_do_update(
        models.SocksServer.__table__.primary_key, set_=dict(status=socks_server.status)
    )
    # await db.execute(q)
    result = await db.scalars(
        q.returning(models.SocksServer), execution_options={"populate_existing": True}
    )
    await db.commit()
    return result.unique().one()


@redis_cache(
    key_prefix="socks_server",
    session_factory=SessionLocal,
    schema=schemas.SocksServer,  # Ensure this schema exists
    key_param_name="id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_socks_server(db: AsyncSession, id: UUID4) -> Optional[models.SocksServer]:
    return await db.get(models.SocksServer, id)


async def list_socks_servers_paged(
    db: AsyncSession, filters: filters.SocksServerFilter
):
    q: Select = select(models.SocksServer)
    q = q.outerjoin(models.SocksServer.labels)
    q = filters.filter(q)  # type: ignore
    try:
        q = filters.sort(q)  # type: ignore
    except NotImplementedError:
        pass
    q = q.group_by(models.SocksServer.id)
    return await paginate(db, q)


async def get_socks_servers(
    db: AsyncSession,
    filters: filters.SocksServerFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.SocksServer]:
    q: Select = select(models.SocksServer)
    q = q.outerjoin(models.SocksServer.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def update_socks_server_status(db: AsyncSession, id: UUID4, status: str) -> None:
    q = (
        update(models.SocksServer)
        .where(models.SocksServer.id == id)
        .values(status=status)
    )
    await db.execute(q)
    await db.commit()


async def get_socks_server_filters(
    db: AsyncSession, filters: filters.SocksServerFilter
):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.SocksServer.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    # create filters for operating system, type and status
    for field in ["operating_system", "type", "status"]:
        res = await create_filter_for_column(
            db, q, getattr(models.SocksServer, field), field, field
        )
        result.append(res)

    return result


async def get_actions_paged(
    db: AsyncSession, filters: filters.ActionFilter
) -> Page[models.Action]:
    q: Select = select(models.Action)
    q = q.outerjoin(models.Action.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.Action.id)
    return await paginate(db, q)


async def get_action_filters(db: AsyncSession, filters: filters.ActionFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Action.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    # create filters for operating system, type and status
    for field in ["status"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Action, field), field, field
        )
        result.append(res)

    return result


async def get_action(db: AsyncSession, id: UUID4) -> Optional[models.Action]:
    return await db.get(models.Action, id)


async def delete_action_playbook_mapping(
    db: AsyncSession, action_id: UUID4 | str
) -> None:
    q = delete(models.ActionPlaybook).where(
        models.ActionPlaybook.action_id == action_id
    )
    await db.execute(q)
    await db.commit()


async def add_action_playbook_mapping(
    db: AsyncSession, action_id: UUID4 | str, playbook_template_id: UUID4 | str
) -> bool:
    q = insert(models.ActionPlaybook).values(
        action_id=action_id, playbook_template_id=playbook_template_id
    )
    try:
        await db.execute(q)
        await db.commit()
        return True
    except IntegrityError:
        await db.rollback()
        return False


async def create_action(db: AsyncSession, action: schemas.ActionCreate) -> None:
    q = (
        insert(models.Action)
        .values(**action.model_dump(exclude={"labels", "playbook_template_ids"}))
        .values(time_created=func.now())
    )
    q = q.on_conflict_do_update(
        models.Action.__table__.primary_key,
        set_=dict(
            name=action.name, description=action.description, time_updated=func.now()
        ),
    )
    # await db.execute(q)
    result: models.Action = await db.scalars(
        q.returning(models.Action), execution_options={"populate_existing": True}
    )  # type: ignore

    await db.commit()

    await delete_label_item(db, schemas.LabeledItemDelete(action_id=action.id))
    for entry in action.labels or []:
        label = await get_label_by_name(db, entry)
        if not label:
            label = await create_label(
                db,
                schemas.LabelCreate(name=entry, category="Playbooks"),
            )
        await create_label_item(
            db,
            schemas.LabeledItemCreate(
                label_id=label.id,
                action_id=action.id,
            ),
        )

    await delete_action_playbook_mapping(db, action.id)

    for template_id in action.playbook_template_ids or []:
        added = await add_action_playbook_mapping(
            db, action_id=action.id, playbook_template_id=template_id
        )
    await db.commit()


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
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.CertificateTemplate.id)

    q = await _apply_permission_filter(q, "Enroll", enroll_permissions)
    q = await _apply_permission_filter(q, "Owner", owner_permissions)
    q = await _apply_permission_filter(q, "WriteOwner", writeowner_permissions)
    q = await _apply_permission_filter(q, "FullControl", fullcontrol_permissions)
    q = await _apply_permission_filter(q, "WriteDACL", writedacl_permissions)
    q = await _apply_permission_filter(q, "WriteProperty", writeproperty_permissions)

    return await paginate(db, q)


async def _apply_permission_filter(
    q: Select,
    permission_type: str,
    permission_value: str
) -> Select:
    """
    Applies a permission filter to the query using a table alias to prevent conflicts.

    Args:
        q: The current SQLAlchemy Select query.
        permission_type: The type of permission (e.g., "Enroll", "Owner").
        permission_value: The principal associated with the permission.

    Returns:
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
    q = filters.filter(q)  # type: ignore

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
            db, q, getattr(models.CertificateTemplate, field), field, field
        )
        result.append(res)

    permissions = ["Owner", "WriteOwner", "FullControl", "WriteDacl", "Enroll", "WriteProperty"]
    for permission_type in permissions:
        permission_filter = await create_certificate_permission_filter(db, q, permission_type)
        result.append(permission_filter)
        
    return result


async def create_certificate_permission_filter(
    db: AsyncSession, q: Select, permission_type: str
) -> schemas.Filter:
    """
    Creates a filter option list for a given permission type based on the main query's results.
    """
    # Create a subquery that gets the IDs of all certificate templates
    # that match the main query's filters.
    template_ids_subquery = q.with_only_columns(
        models.CertificateTemplate.id
    ).distinct().subquery()

    # Now, create a NEW, separate query to find principals for the specified
    # permission type, but only for the templates identified by the subquery.
    permissions_q = (
        select(
            func.count(models.CertificateTemplatePermission.principal).label("count"),
            models.CertificateTemplatePermission.principal,
        )
        .where(
            # Filter permissions to only those related to our templates
            models.CertificateTemplatePermission.certificate_template_id.in_(
                select(template_ids_subquery)
            )
        )
        .where(models.CertificateTemplatePermission.permission == permission_type)
        .group_by(models.CertificateTemplatePermission.principal)
    )

    options: list[schemas.FilterOption] = []
    res = await db.execute(permissions_q)
    for count, principal in res.all():
        if principal is not None:
            options.append(schemas.FilterOption(name=str(principal), count=count))

    ft_entry = schemas.Filter(
        name=f"{permission_type.lower()}_permissions",
        icon="",
        type="options",
        options=options,
        query_name=f"{permission_type.lower()}_permissions",
    )

    return ft_entry


async def get_certificate_template(
    db: AsyncSession, id: UUID4
) -> Optional[models.CertificateTemplate]:
    return await db.get(models.CertificateTemplate, id)


async def get_certificate_authorities(
    db: AsyncSession,
    filters: filters.CertificateAuthorityFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.CertificateAuthority]:
    q: Select = select(models.CertificateAuthority)
    q = q.outerjoin(models.CertificateAuthority.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.CertificateAuthority.id)
    q = q.offset(offset)
    q = q.limit(limit)
    result = await db.execute(q)
    return result.unique().scalars().all()


async def create_certificate_template(
    db: AsyncSession, certificate_template: schemas.CertificateTemplateCreate
) -> Tuple[bool, models.CertificateTemplate]:
    data = certificate_template.model_dump()
    authorities = data.pop("certificate_authorities")

    # q = insert(models.CertificateTemplate).values(**data)
    # data["time_updated"] = func.now()
    # update_stmt = q.on_conflict_do_update(
    #     "certificate_templates_template_name_key", set_=data
    # )
    # res = await db.scalars(
    #     update_stmt.returning(models.CertificateTemplate),
    #     execution_options={"populate_existing": True},
    # )
    template_db = models.CertificateTemplate(**data)
    db.add(template_db)
    await db.commit()
    await db.refresh(template_db)
    await send_event(
        schemas.Event.certificate_template, schemas.EventType.new, template_db.id
    )
    # result = res.unique().one()
    # if result.time_updated == None:
    #     await send_event(
    #         schemas.Event.certificate_template, schemas.EventType.new, result.id
    #     )
    for authority in authorities or []:
        auth_db = list(
            await get_certificate_authorities(
                db, filters.CertificateAuthorityFilter(ca_name=authority), 0, 1
            )
        )
        if auth_db:
            await create_certificate_authority_map(db, auth_db[0].id, template_db.id)
    return True, template_db


async def create_certificate_authority_map(
    db: AsyncSession,
    certificate_authority_id: UUID4 | str,
    certificate_template_id: UUID4 | str,
) -> None:
    q = insert(models.CertificateAuthorityMap).values(
        certificate_authority_id=certificate_authority_id,
        certificate_template_id=certificate_template_id,
    )
    update_stmt = q.on_conflict_do_nothing(
        "authority_template_id_uc",
    )
    await db.execute(update_stmt)
    await db.commit()


async def get_certificate_authorities_paged(
    db: AsyncSession, filters: filters.CertificateAuthorityFilter
) -> Page[models.CertificateAuthority]:
    q: Select = select(models.CertificateAuthority)
    q = q.outerjoin(models.CertificateAuthority.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.CertificateAuthority.id)
    return await paginate(db, q)


async def get_certificate_authorities_filters(
    db: AsyncSession, filters: filters.CertificateAuthorityFilter
):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.CertificateAuthority.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in ["ca_name", "dns_name"]:
        res = await create_filter_for_column(
            db, q, getattr(models.CertificateAuthority, field), field, field
        )
        result.append(res)

    return result


async def get_certificate_authority(
    db: AsyncSession, id: UUID4
) -> Optional[models.CertificateAuthority]:
    return await db.get(models.CertificateAuthority, id)


async def create_certificate_authority(
    db: AsyncSession, certificate_authority: schemas.CertificateAuthorityCreate
) -> Tuple[bool, models.CertificateAuthority]:
    data = certificate_authority.model_dump()
    q = insert(models.CertificateAuthority).values(**data)
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update("ca_dns_name_uc", set_=data)
    res = await db.scalars(
        update_stmt.returning(models.CertificateAuthority),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = res.unique().one()
    if result.time_updated == None:
        await send_event(
            schemas.Event.certificate_authority, schemas.EventType.new, result.id
        )
    return result.time_updated == None, result


async def create_certificate_template_permissions(
    db: AsyncSession,
    certificate_template_permissions: schemas.CertificateTemplatePermissionCreate,
) -> Tuple[bool, models.CertificateTemplatePermission]:
    data = certificate_template_permissions.model_dump()
    q = insert(models.CertificateTemplatePermission).values(**data)
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update(
        "certificate_template_permissions_uc", set_=data
    )
    result = await db.scalars(
        update_stmt.returning(models.CertificateTemplatePermission),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    if result.time_updated == None:
        await send_event(
            schemas.Event.certificate_template_permissions,
            schemas.EventType.new,
            result.id,
        )
    return result.time_updated == None, result


async def get_issues_paged(
    db: AsyncSession, filters: filters.IssueFilter
) -> Page[models.Issue]:
    q: Select = select(models.Issue)
    q = q.outerjoin(models.Issue.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.Issue.id)
    return await paginate(db, q)


async def get_issue_filters(db: AsyncSession, filters: filters.IssueFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Issue.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    for field in ["impact", "exploitability"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Issue, field), field, field
        )
        result.append(res)

    return result


async def get_issue(db: AsyncSession, id: UUID4) -> Optional[models.Issue]:
    return await db.get(models.Issue, id)


async def create_issue(
    db: AsyncSession, issues: schemas.IssueCreate
) -> Tuple[bool, models.Issue]:
    data = issues.model_dump()
    q = insert(models.Issue).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update("issues_name_key", set_=data)
    result = await db.scalars(
        update_stmt.returning(models.Issue),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    if result.time_updated == None:
        await send_event(schemas.Event.issue, schemas.EventType.new, result.id)
    return result.time_updated == None, result

@redis_cache_invalidate(
    key_prefix="issue",
    key_param_name="id",
)
async def update_issue(
    db: AsyncSession, id: str | uuid.UUID, issue: schemas.IssueCreate
) -> None:
    q = update(models.Issue).where(models.Issue.id == id).values(**issue.model_dump())
    await db.execute(q)
    await db.commit()


async def create_manual_timeline_task(
    db: AsyncSession, manual_timeline_tasks: schemas.ManualTimelineTaskCreate
) -> models.ManualTimelineTask:
    result = models.ManualTimelineTask(**manual_timeline_tasks.model_dump())
    db.add(result)
    await db.commit()
    await db.refresh(result)
    return result


async def update_manual_timeline_task(
    db: AsyncSession,
    id: str | uuid.UUID,
    manual_timeline_tasks: schemas.ManualTimelineTaskCreate,
) -> None:
    q = (
        update(models.ManualTimelineTask)
        .where(models.ManualTimelineTask.id == id)
        .values(**manual_timeline_tasks.model_dump())
    )
    await db.execute(q)
    await db.commit()


async def get_file_by_hash(db: AsyncSession, hash_value: str) -> Optional[models.File]:
    hash_value = hash_value.lower()
    q = await db.execute(
        select(models.File).where(
            or_(
                models.File.md5sum == hash_value,
                models.File.sha1sum == hash_value,
                models.File.sha256sum == hash_value,
            )
        )
    )
    return q.scalars().first()


async def get_c2_server_types_paged(
    db: AsyncSession, filters: filters.C2ServerTypeFilter
) -> Page[models.C2ServerType]:
    q: Select = select(models.C2ServerType)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.C2ServerType.id)
    return await paginate(db, q)


async def get_c2_server_types(
    db: AsyncSession, id: UUID4
) -> Optional[models.C2ServerType]:
    return await db.get(models.C2ServerType, id)


async def create_c2_server_type(
    db: AsyncSession, c2_server_types: schemas.C2ServerTypeCreate
) -> Tuple[bool, models.C2ServerType]:
    data = c2_server_types.model_dump()
    q = insert(models.C2ServerType).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update(
        models.C2ServerType.__table__.primary_key, set_=data
    )
    result = await db.scalars(
        update_stmt.returning(models.C2ServerType),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    if result.time_updated == None:
        await send_event(schemas.Event.c2_server_type, schemas.EventType.new, result.id)
    return result.time_updated == None, result


async def update_c2_server_type(
    db: AsyncSession, id: str | uuid.UUID, c2_server_types: schemas.C2ServerTypeCreate
) -> None:
    q = (
        update(models.C2ServerType)
        .where(models.C2ServerType.id == id)
        .values(**c2_server_types.model_dump())
    )
    await db.execute(q)
    await db.commit()


async def get_c2_server_type_by_name(
    db: AsyncSession, name: str
) -> Optional[models.C2ServerType]:
    q: Select = select(models.C2ServerType)
    q = q.where(models.C2ServerType.name == name)
    res = await db.execute(q)
    return res.scalars().first()


async def get_c2_server_arguments_paged(
    db: AsyncSession, c2_server_type: UUID4
) -> Page[models.C2ServerArguments]:
    q: Select = select(models.C2ServerArguments)
    q = q.where(models.C2ServerArguments.c2_server_type_id == c2_server_type)
    return await paginate(db, q)


async def get_c2_server_arguments(
    db: AsyncSession, id: UUID4
) -> Optional[models.C2ServerArguments]:
    return await db.get(models.C2ServerArguments, id)


async def create_c2_server_argument(
    db: AsyncSession, c2_server_argument: schemas.C2ServerArgumentsCreate
) -> Tuple[bool, models.C2ServerArguments]:
    data = c2_server_argument.model_dump()
    q = insert(models.C2ServerArguments).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update(
        models.C2ServerArguments.__table__.primary_key, set_=data
    )
    result = await db.scalars(
        update_stmt.returning(models.C2ServerArguments),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    return result.time_updated == None, result


async def delete_c2_server_arguments(
    db: AsyncSession, c2_server_type_id: UUID4
) -> None:
    q = delete(models.C2ServerArguments).where(
        models.C2ServerArguments.c2_server_type_id == c2_server_type_id
    )
    await db.execute(q)
    await db.commit()


async def get_suggestions_paged(
    db: AsyncSession, filters: filters.SuggestionFilter
) -> Page[models.Suggestion]:
    q: Select = select(models.Suggestion)
    q = q.outerjoin(models.Suggestion.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.Suggestion.id)
    return await paginate(db, q)


async def get_suggestions(
    db: AsyncSession,
    filters: filters.SuggestionFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Suggestion]:
    q: Select = select(models.Suggestion)
    q = q.outerjoin(models.Suggestion.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_suggestions_filters(db: AsyncSession, filters: filters.SuggestionFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Suggestion.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in ["name"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Suggestion, field), field, field
        )
        result.append(res)

    return result


@redis_cache(
    key_prefix="suggestion",
    session_factory=SessionLocal,
    schema=schemas.Suggestion,  # Ensure this schema exists
    key_param_name="id",
    ttl_seconds=DEFAULT_CACHE_TTL,
)
async def get_suggestion(db: AsyncSession, id: UUID4) -> Optional[models.Suggestion]:
    return await db.get(models.Suggestion, id)


async def create_suggestion(
    db: AsyncSession, suggestions: schemas.SuggestionCreate
) -> Tuple[bool, models.Suggestion]:
    data = suggestions.model_dump()
    q = insert(models.Suggestion).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update(
        models.Suggestion.__table__.primary_key, set_=data
    )
    result = await db.scalars(
        update_stmt.returning(models.Suggestion),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    if result.time_updated == None:
        await send_event(schemas.Event.suggestion, schemas.EventType.new, result.id)
    return result.time_updated == None, result


async def update_suggestion(
    db: AsyncSession, id: str | uuid.UUID, suggestions: schemas.SuggestionCreate
) -> None:
    q = (
        update(models.Suggestion)
        .where(models.Suggestion.id == id)
        .values(**suggestions.model_dump())
    )
    await db.execute(q)
    await db.commit()


async def get_checklists_paged(
    db: AsyncSession, filters: filters.ChecklistFilter
) -> Page[models.Checklist]:
    q: Select = select(models.Checklist)
    q = q.outerjoin(models.Checklist.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.Checklist.id)
    return await paginate(db, q)


async def get_checklists(
    db: AsyncSession,
    filters: filters.ChecklistFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Checklist]:
    q: Select = select(models.Checklist)
    q = q.outerjoin(models.Checklist.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_checklists_filters(db: AsyncSession, filters: filters.ChecklistFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Checklist.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in ["phase", "name", "status"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Checklist, field), field, field
        )
        result.append(res)

    return result


async def get_checklist(db: AsyncSession, id: UUID4) -> Optional[models.Checklist]:
    return await db.get(models.Checklist, id)


async def create_checklist(
    db: AsyncSession, checklists: schemas.ChecklistCreate
) -> Tuple[bool, models.Checklist]:
    data = checklists.model_dump()
    q = insert(models.Checklist).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    if checklists.c2_implant_id:
        update_stmt = q.on_conflict_do_update("checklist_implant_phase_name", set_=data)
    else:
        update_stmt = q.on_conflict_do_update("checklist_domain_phase_name", set_=data)
    result = await db.scalars(
        update_stmt.returning(models.Checklist),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    if result.time_updated == None:
        await send_event(schemas.Event.checklist, schemas.EventType.new, result.id)
    return result.time_updated == None, result


async def update_checklist(
    db: AsyncSession, id: str | uuid.UUID, checklists: schemas.ChecklistCreate
) -> None:
    q = (
        update(models.Checklist)
        .where(models.Checklist.id == id)
        .values(**checklists.model_dump())
    )
    await db.execute(q)
    await db.commit()


async def get_objectives_paged(
    db: AsyncSession, filters: filters.ObjectivesFilter
) -> Page[models.Objectives]:
    q: Select = select(models.Objectives)
    q = q.outerjoin(models.Objectives.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.group_by(models.Objectives.id)
    return await paginate(db, q)


async def get_objectives(
    db: AsyncSession,
    filters: filters.ObjectivesFilter,
    offset: int = 0,
    limit: int = 10,
) -> Iterable[models.Objectives]:
    q: Select = select(models.Objectives)
    q = q.outerjoin(models.Objectives.labels)
    q = filters.filter(q)  # type: ignore
    q = filters.sort(q)  # type: ignore
    q = q.offset(offset).limit(limit)
    result = await db.execute(q)
    return result.scalars().unique().all()


async def get_objectives_filters(db: AsyncSession, filters: filters.ObjectivesFilter):
    result: list[schemas.Filter] = []
    q: Select = (
        select(func.count(models.Objectives.id.distinct()).label("count_1"))
        .outerjoin(models.LabeledItem)
        .outerjoin(models.Label)
    )
    q = filters.filter(q)  # type: ignore

    lb_entry = await get_labels_for_q(db, q)
    result.extend(lb_entry)

    for field in ["status"]:
        res = await create_filter_for_column(
            db, q, getattr(models.Objectives, field), field, field
        )
        result.append(res)

    return result


async def get_objective(db: AsyncSession, id: UUID4) -> Optional[models.Objectives]:
    return await db.get(models.Objectives, id)


async def create_objective(
    db: AsyncSession, objective: schemas.ObjectiveCreate
) -> Tuple[bool, models.Objectives]:
    data = objective.model_dump()
    q = insert(models.Objectives).values(**data).values(time_created=func.now())
    data["time_updated"] = func.now()
    update_stmt = q.on_conflict_do_update(
        models.Objectives.__table__.primary_key, set_=data
    )
    result = await db.scalars(
        update_stmt.returning(models.Objectives),
        execution_options={"populate_existing": True},
    )
    await db.commit()
    result = result.unique().one()
    if result.time_updated == None:
        await send_event(schemas.Event.objective, schemas.EventType.new, result.id)
    return result.time_updated == None, result


async def update_objective(
    db: AsyncSession, id: str | uuid.UUID, objective: schemas.ObjectiveCreate
) -> None:
    q = (
        update(models.Objectives)
        .where(models.Objectives.id == id)
        .values(**objective.model_dump())
    )
    await db.execute(q)
    await db.commit()
