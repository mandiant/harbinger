import asyncio
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from alembic import command
from alembic.config import Config
from fastapi_users.authentication.strategy.redis import RedisStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from testcontainers.core.utils import inside_container
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from harbinger import models, schemas
from harbinger.config import get_settings
from harbinger.config.app import app
from harbinger.config.dependencies import get_db
from harbinger.database.database import get_async_session
from harbinger.database.users import (
    UserManager,
    get_redis_strategy,
)


# --- 1. Container and Core Infrastructure (Session-Scoped) ---
class FixedPostgresContainer(PostgresContainer):
    """A PostgresContainer that correctly determines the host IP when running inside a container."""

    def get_container_host_ip(self) -> str:
        host = super().get_container_host_ip()
        if host == "localhost" and inside_container():
            return self.get_docker_client().gateway_ip(self._container.id)
        return host


class FixedRedisContainer(RedisContainer):
    """A RedisContainer that correctly determines the host IP when running inside a container."""

    def get_container_host_ip(self) -> str:
        host = super().get_container_host_ip()
        if host == "localhost" and inside_container():
            return self.get_docker_client().gateway_ip(self._container.id)
        return host


@pytest.fixture(scope="session")
def pg_dsn() -> Generator[str, None, None]:
    """Starts a PostgreSQL container once per test session and yields its DSN."""
    with FixedPostgresContainer("postgres:15-alpine", driver="asyncpg") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="session")
def redis_dsn() -> Generator[str, None, None]:
    """Starts a Redis container once per test session and yields its DSN."""
    with FixedRedisContainer("redis:7") as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(redis.port)
        yield f"redis://{host}:{port}"


@pytest.fixture(scope="session")
def event_loop():
    """Creates a single event loop for the entire test session for consistency."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine(migrated_db: str) -> AsyncGenerator[AsyncEngine, None]:
    """
    Creates a single database engine for the entire test session.
    Depends on 'migrated_db' to ensure migrations have run.
    """
    db_engine = create_async_engine(migrated_db, poolclass=NullPool)
    yield db_engine
    await db_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def migrated_db(pg_dsn: str, redis_dsn: str) -> AsyncGenerator[str, None]:
    """
    Patches application settings, runs migrations up to 'head', and yields the DSN.
    """
    assert pg_dsn, "PostgreSQL container failed to start!"
    assert redis_dsn, "Redis container failed to start!"

    with patch("harbinger.config.get_settings") as mock_get_settings:
        mock_settings = get_settings()
        mock_settings.pg_dsn = pg_dsn
        mock_settings.redis_dsn = redis_dsn
        mock_get_settings.return_value = mock_settings

        alembic_cfg = Config()
        script_location = Path(__file__).parent.parent / "alembic"
        alembic_cfg.set_main_option("script_location", str(script_location))
        alembic_cfg.set_main_option("sqlalchemy.url", pg_dsn.replace("+asyncpg", ""))

        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
        yield pg_dsn
        await asyncio.to_thread(command.downgrade, alembic_cfg, "base")


# --- 2. Per-Test Transactional Fixtures (Function-Scoped) ---
@pytest_asyncio.fixture(scope="function")
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a session wrapped in a transaction that is rolled back.
    """
    async with engine.connect() as connection:
        await connection.begin()
        session_maker = async_sessionmaker(bind=connection)
        session = session_maker()
        yield session
        await connection.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Provides a client with the database session dependency overridden.
    """
    # CORRECTED: Override the correct dependency, 'get_db'
    app.dependency_overrides[get_db] = lambda: db_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    # CORRECTED: Clean up the correct override
    del app.dependency_overrides[get_db]


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(
    db_session: AsyncSession,
    redis_dsn: str,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Provides an authenticated client, handling all necessary dependency
    overrides before the client is created.
    """

    # 1. Set up and override dependencies
    def get_test_db():
        return db_session

    redis_client = await aioredis.from_url(redis_dsn, decode_responses=True)
    strategy = RedisStrategy(redis_client, lifetime_seconds=3600)

    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_async_session] = get_test_db
    app.dependency_overrides[get_redis_strategy] = lambda: strategy

    # 2. Create the user inside a savepoint (nested transaction)
    user_db = SQLAlchemyUserDatabase(db_session, models.User)
    user_manager = UserManager(user_db)
    user_in = schemas.UserCreate(
        email="test@example.com",
        password="password123",
        is_active=True,
        is_superuser=True,
        is_verified=True,
    )

    user = await user_manager.create(user_in)

    await db_session.refresh(user)

    token = await strategy.write_token(user)

    # 3. Create the client now that everything is configured
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        c.cookies["fastapiusersauth"] = token
        yield c

    # 4. Teardown
    await redis_client.aclose()
    del app.dependency_overrides[get_db]
    del app.dependency_overrides[get_async_session]
    del app.dependency_overrides[get_redis_strategy]
