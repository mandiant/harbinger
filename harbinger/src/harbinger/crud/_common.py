import asyncio
import logging
import random
import string

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from jinja2 import PackageLoader
from jinja2.ext import do
from jinja2.sandbox import SandboxedEnvironment
from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.expression import func

from harbinger import models, schemas
from harbinger.database.cache import invalidate_cache_entry, redis_cache_fixed_key
from harbinger.database.database import SessionLocal, get_async_session

CACHE_DECORATORS_AVAILABLE = True

DEFAULT_CACHE_TTL = 3600

logger = logging.getLogger(__name__)


def filter_shuffle(seq):
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except Exception:
        return seq


env = SandboxedEnvironment(
    enable_async=True,
    autoescape=False,
    loader=PackageLoader("harbinger.job_templates", "templates"),
    extensions=[do],
)


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
        if entry[1] or entry[1] is False:
            options.append(schemas.FilterOption(name=str(entry[1]), count=entry[0]))
    return schemas.Filter(
        name=name,
        icon="",
        type="options",
        options=options,
        query_name=query_name,
    )


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, models.User)


def divmod_excel(n: int) -> tuple[int, int]:
    a, b = divmod(n, 26)
    if b == 0:
        return (a - 1, b + 26)
    return (a, b)


def to_excel(num: int) -> str:
    chars = []
    while num > 0:
        num, d = divmod_excel(num)
        chars.append(string.ascii_uppercase[d - 1])
    return "".join(reversed(chars))


async def get_database_statistics(db: AsyncSession) -> dict[str, int]:
    """Efficiently retrieves counts of key models from the database."""
    queries = {
        "C2 Implants": select(func.count(models.C2Implant.id)),
        "Credentials": select(func.count(models.Credential.id)),
        "Hosts": select(func.count(models.Host.id)),
        "Playbook Templates": select(func.count(models.PlaybookTemplate.id)),
        "Domains": select(func.count(models.Domain.id)),
        "Shares": select(func.count(models.Share.id)),
        "Files": select(func.count(models.File.id)),
        "C2 Tasks": select(func.count(models.C2Task.id)),
        "Proxy Jobs": select(func.count(models.ProxyJob.id)),
        "Suggestions": select(func.count(models.Suggestion.id)),
    }
    tasks = [db.scalar(query) for query in queries.values()]
    results = await asyncio.gather(*tasks)
    return dict(zip(queries.keys(), results, strict=False))


@redis_cache_fixed_key(
    cache_key="job_statistics",
    session_factory=SessionLocal,
    schema=schemas.StatisticsItems,
)
async def get_job_statistics(db: AsyncSession) -> dict:
    stats = {}
    q = select(models.ProxyJob.status, func.count(models.ProxyJob.id)).group_by(
        models.ProxyJob.status,
    )
    result = await db.execute(q)
    for entry in result.all():
        if entry[0]:
            stats[entry[0]] = entry[1]
    q = select(models.C2Job.status, func.count(models.C2Job.id)).group_by(
        models.C2Job.status,
    )
    result = await db.execute(q)
    for entry in result.all():
        if entry[0] in stats:
            stats[entry[0]] += entry[1]
        else:
            stats[entry[0]] = entry[1]
    return {"items": [{"key": key, "value": value} for key, value in stats.items()]}


def create_random_color():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


async def send_label_events(
    label: schemas.LabeledItemCreate | schemas.LabeledItemDelete,
) -> None:
    dumped_label = label.model_dump(exclude_unset=True)
    dumped_label.pop("label_id", None)
    for key, value in dumped_label.items():
        if value is not None and key.endswith("_id"):
            key_prefix = key.replace("_id", "")
            try:
                await invalidate_cache_entry(key_prefix=key_prefix, key_value=value)
            except Exception as e:
                logger.error(
                    f"Error during cache invalidation call for {key_prefix}:{value}: {e}",
                    exc_info=True,
                )
