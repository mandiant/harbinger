import asyncio
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from fastapi_users.db import SQLAlchemyUserDatabase
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
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
    auth_backend_cookie,
    get_redis_strategy,
)


class FixedPostgresContainer(PostgresContainer):
    """A PostgresContainer that correctly determines the host IP when running inside another container."""

    def get_container_host_ip(self) -> str:
        if inside_container() and Path("/run/docker.sock").exists():
            return self.get_docker_client().gateway_ip(self._container.id)
        return super().get_container_host_ip()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def pg_dsn():
    """Starts a PostgreSQL container and returns the DSN."""
    with FixedPostgresContainer("postgres:14", driver="asyncpg") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="session")
def redis_dsn():
    """Starts a Redis container and returns the DSN."""
    with RedisContainer("redis:7") as redis:
        host = "localhost"
        port = redis.get_exposed_port(6379)
        yield f"{host}:{port}"


@pytest_asyncio.fixture(scope="session", autouse=True)
async def migrated_db(pg_dsn, redis_dsn):
    """
    Patches the application's settings to use the test database and runs migrations.
    The `autouse=True` flag ensures this fixture is used for all tests.
    """
    original_settings = get_settings()
    original_settings.pg_dsn = pg_dsn
    original_settings.redis_dsn = f"redis://{redis_dsn}"

    redis_client = AsyncRedis.from_url(original_settings.redis_dsn, decode_responses=True)
    redis_no_decode_client = AsyncRedis.from_url(original_settings.redis_dsn, decode_responses=False)

    with (
        patch("harbinger.database.database.get_settings", return_value=original_settings),
        patch("harbinger.database.redis_pool.get_settings", return_value=original_settings, create=True),
        patch("harbinger.database.users.get_settings", return_value=original_settings),
        patch(
            "harbinger.database.users.redis",
            redis_client,
        ),
        patch(
            "harbinger.database.redis_pool.redis_no_decode",
            redis_no_decode_client,
        ),
    ):
        sync_psql_url = pg_dsn.replace("+asyncpg", "")
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", str(Path(__file__).parent / ".." / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", sync_psql_url)

        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
        yield pg_dsn
        await asyncio.to_thread(command.downgrade, alembic_cfg, "base")

    await redis_client.aclose()
    await redis_no_decode_client.aclose()


@pytest_asyncio.fixture(scope="function")
async def db_session(pg_dsn):
    """
    Provides a transactional SQLAlchemy session for interacting with the test database.
    """
    engine = create_async_engine(pg_dsn)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

    async with TestingSessionLocal() as session:
        await session.begin()
        yield session
        await session.rollback()

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """
    Provides a FastAPI TestClient that is configured to use the test database session.
    """
    import httpx

    async def override_get_db():
        return db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_async_session] = override_get_db
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_async_session, None)


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client: httpx.AsyncClient, db_session: AsyncSession):
    """
    Provides an authenticated client by creating a user and setting an auth cookie directly.
    """
    user_db = SQLAlchemyUserDatabase(db_session, models.User)
    user_manager = UserManager(user_db)
    strategy = get_redis_strategy()

    email = "test@example.com"
    password = "password"
    try:
        user = await user_manager.get_by_email(email)
    except Exception:
        user = None

    if not user:
        user = await user_manager.create(
            schemas.UserCreate(
                email=email,
                password=password,
                is_active=True,
                is_superuser=True,
                is_verified=True,
            )
        )

    token = await strategy.write_token(user)
    client.cookies[auth_backend_cookie.name] = token
    return client
