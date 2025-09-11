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

import os
import uuid
import unittest
from pathlib import Path
from unittest import mock
import asyncio
import copy  # Import copy module
import importlib  # Import importlib


from redis import asyncio as aioredis
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from testcontainers.core.utils import inside_container
from alembic.config import Config
from alembic import command
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Assume these are your application modules
from harbinger import schemas
from harbinger import crud
from harbinger import filters
from harbinger.database import database  # Import database module itself
from harbinger.config import get_settings  # Import the original get_settings
# Assuming redis_cache and its 'redis' client are here - ADJUST IF NECESSARY
# from harbinger.common.cache import redis_cache, redis # Example path

here = Path(os.path.dirname(os.path.abspath(__file__)))


# --- Helper Function for Async Cleanup ---
# unittest.IsolatedAsyncioTestCase doesn't run async cleanup functions automatically
# See: https://bugs.python.org/issue41837
# This helper ensures async cleanup happens correctly.
def async_safe_add_cleanup(test_instance, coro):
    """Adds an awaitable cleanup function that runs reliably."""
    loop = asyncio.get_event_loop()
    test_instance.addCleanup(lambda: loop.run_until_complete(coro()))


class FixedPostgresContainer(PostgresContainer):
    def get_container_host_ip(self) -> str:
        if inside_container() and Path("/run/docker.sock").exists():
            return self.get_docker_client().gateway_ip(self._container.id)
        return super().get_container_host_ip()


class FixedRedisContainer(RedisContainer):
    def get_container_host_ip(self) -> str:
        if inside_container() and Path("/run/docker.sock").exists():
            return self.get_docker_client().gateway_ip(self._container.id)
        return super().get_container_host_ip()


class TestCrud(unittest.IsolatedAsyncioTestCase):
    # No need for custom __init__ in IsolatedAsyncioTestCase
    # def __init__(self, methodName):
    #     super().__init__(methodName)
    #     self.postgres = None # Initialize here
    #     self.redis_container = None # Initialize here
    #     self.test_redis_client = None # Initialize here

    async def asyncSetUp(self):
        self.postgres = None
        self.redis_container = None
        self.test_redis_client = None
        self.settings_patcher = None
        self.redis_patcher = None
        self.mock_settings = None
        self.mock_redis = None

        try:
            # --- Start Containers ---
            print("Starting PostgreSQL container...")
            self.postgres = FixedPostgresContainer(
                "postgres:14",
                driver="asyncpg",
                username="postgres",
                password="postgres",
                dbname="postgres",
                port=5432,
            )
            self.postgres.start()
            psql_url = self.postgres.get_connection_url()
            print(f"Explicit PostgreSQL URL: {psql_url}")
            async_safe_add_cleanup(self, self._stop_postgres)

            print("Starting Redis container...")
            self.redis_container = FixedRedisContainer("redis:latest")
            self.redis_container.start()
            redis_host = self.redis_container.get_container_host_ip()
            redis_port = self.redis_container.get_exposed_port(6379)
            redis_url = f"redis://{redis_host}:{redis_port}"
            print(f"Redis started: {redis_url}")
            async_safe_add_cleanup(self, self._stop_redis)

            # --- Configure Environment ---
            os.environ["pg_dsn"] = psql_url
            os.environ["redis_dsn"] = redis_url
            # ... other os.environ settings ...
            get_settings.cache_clear()

            # --- **PATCH SETTINGS FIRST** ---
            print("Patching harbinger.database.database.get_settings...")
            original_settings = get_settings()
            self.mock_settings_obj = copy.deepcopy(original_settings)
            self.mock_settings_obj.pg_dsn = psql_url

            self.settings_patcher = mock.patch(
                "harbinger.database.database.get_settings",  # Patch where it's used in database.py
                return_value=self.mock_settings_obj,
            )
            self.mock_settings = self.settings_patcher.start()
            self.addCleanup(self.settings_patcher.stop)
            print("Settings patched.")

            # --- Force Reload relevant modules ---
            print("Reloading database module to apply patched settings...")
            importlib.reload(
                database
            )  # Reload database to re-create engine/SessionLocal
            print("Reloading crud module to re-apply decorators...")
            importlib.reload(
                crud
            )  # Reload crud to make decorators capture new SessionLocal
            print("Modules reloaded.")

            # --- Database Migrations ---
            print("Running Alembic migrations...")
            alembic_cfg = Config()
            alembic_cfg.set_main_option("script_location", str(here / ".." / "alembic"))
            sync_psql_url = psql_url.replace("+asyncpg", "")
            alembic_cfg.set_main_option("sqlalchemy.url", sync_psql_url)
            await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
            print("Alembic upgrade complete.")

            # --- Setup Test Database Session (using the reloaded SessionLocal) ---
            # Use the SessionLocal from the *reloaded* database module
            self.SessionLocal = database.SessionLocal
            print(
                f"Using SessionLocal bound to engine: {self.SessionLocal.kw['bind'].url}"
            )  # Verify URL

            # --- Create Test Redis Client ---
            print("Creating test Redis client...")
            self.test_redis_client = aioredis.from_url(redis_url, decode_responses=True)
            await self.test_redis_client.ping()
            print("Test Redis client connected.")
            async_safe_add_cleanup(self, self._close_redis_client)

            # --- Patch Redis Client ---
            # Patch the 'redis' client object used by the 'redis_cache' decorator
            redis_patch_target = "harbinger.database.cache.redis"  # Assumes client is named 'redis' in cache.py
            print(f"Patching Redis client at '{redis_patch_target}'...")
            self.redis_patcher = mock.patch(
                redis_patch_target, new=self.test_redis_client
            )
            self.mock_redis = self.redis_patcher.start()
            self.addCleanup(self.redis_patcher.stop)
            print("Patching complete.")

        except Exception as e:
            print(f"Error during asyncSetUp: {e}")
            # Manually run cleanup if setup fails mid-way
            await self.asyncTearDown()
            raise

    async def asyncTearDown(self):
        """Runs after each test method."""
        print("Running asyncTearDown...")
        # Cleanup functions added with addCleanup/async_safe_add_cleanup run automatically
        # No need to explicitly call stop/close here if using addCleanup
        # If not using addCleanup, you'd do:
        # if self.redis_patcher: self.redis_patcher.stop()
        # if self.session_patcher: self.session_patcher.stop()
        # if self.test_redis_client: await self._close_redis_client()
        # if self.redis_container: await self._stop_redis()
        # if self.postgres: await self._stop_postgres()
        print("asyncTearDown complete.")

    # --- Cleanup Helper Methods ---
    async def _stop_postgres(self):
        if self.postgres:
            print("Stopping PostgreSQL container...")
            try:
                self.postgres.stop()
                print("PostgreSQL container stopped.")
            except Exception as e:
                print(f"Error stopping PostgreSQL container: {e}")
            self.postgres = None

    async def _stop_redis(self):
        if self.redis_container:
            print("Stopping Redis container...")
            try:
                self.redis_container.stop()
                print("Redis container stopped.")
            except Exception as e:
                print(f"Error stopping Redis container: {e}")
            self.redis_container = None

    async def _close_redis_client(self):
        if self.test_redis_client:
            print("Closing test Redis client...")
            try:
                await self.test_redis_client.aclose()
                # Optional: await self.test_redis_client.connection_pool.disconnect()
                print("Test Redis client closed.")
            except Exception as e:
                print(f"Error closing Redis client: {e}")
            self.test_redis_client = None

    # --- Your Test Methods ---

    async def test_domain(self):
        # This test doesn't directly interact with the cache decorator shown
        async with self.SessionLocal() as db:
            domain = await crud.get_or_create_domain(db, "test")
            domain2 = await crud.get_or_create_domain(db, "test")
            self.assertIsNotNone(domain.id)
            self.assertIsNotNone(domain2.id)
            self.assertEqual(domain.id, domain2.id)
            self.assertTrue(await crud.set_long_name(db, domain.id, "test.local"))
            domain3 = await crud.get_domain(domain.id)  # Assuming this is not cached
            self.assertIsNotNone(domain3)
            if domain3:
                self.assertEqual(domain3.long_name, "test.local")

    async def test_password_with_cache(self):
        # Test specifically checks cache interaction
        password_value = f"test_password_{uuid.uuid4()}"  # Unique password per test run
        created_password_id = None

        # 1. Create the password (should trigger DB write and event)
        async with self.SessionLocal() as db:
            password_obj_1 = await crud.get_or_create_password(
                db, password=password_value
            )
            self.assertIsNotNone(password_obj_1.id)
            created_password_id = password_obj_1.id

            # 2. Get the password - First time (Cache MISS)
            # Assuming get_password IS decorated with redis_cache
            # We need to mock the underlying DB fetch within get_password if we want to be sure
            # but checking the cache directly is simpler here.
            print(f"Getting password ID {created_password_id} - expecting cache MISS")
            password_obj_2 = await crud.get_password(created_password_id)
            self.assertIsNotNone(password_obj_2)
            self.assertEqual(password_obj_2.id, created_password_id)
            # Check if it's in Redis (using our test client)
            cached_value = await self.test_redis_client.get(
                f"password:{created_password_id}"
            )
            self.assertIsNotNone(
                cached_value, "Password should be in Redis cache after first get"
            )

            # 3. Get the password - Second time (Cache HIT)
            # To *prove* it's a cache hit, we could mock the DB call inside get_password,
            # or temporarily break the DB connection. A simpler check is that the
            # data comes back correctly without erroring.
            print(
                f"Getting password ID {created_password_id} again - expecting cache HIT"
            )
            password_obj_3 = await crud.get_password(created_password_id)
            self.assertIsNotNone(password_obj_3)
            self.assertEqual(password_obj_3.id, created_password_id)
            # If we mocked the DB fetch inside get_password, we'd assert it wasn't called here.

            # 4. Test get_passwords (assuming this is NOT cached or cached differently)
            async with self.SessionLocal() as db:
                passwords_list = await crud.get_passwords(db, password_value)
                self.assertEqual(len(list(passwords_list)), 1)

    async def test_proxies(self):
        # Assuming create_proxy isn't cached, but get_proxy might be
        proxy_id = None
        async with self.SessionLocal() as db:
            proxy = await crud.create_proxy(
                db,
                schemas.ProxyCreate(
                    port=8080,
                    type=schemas.ProxyType.socks5,
                    status=schemas.ProxyStatus.connected,
                ),
            )
            self.assertIsNotNone(proxy.id)
            proxy_id = proxy.id

            # Optional: Test get_proxy if it exists and is cached
            # if hasattr(crud, 'get_proxy'):
            #     print(f"Getting proxy ID {proxy_id} - check cache behavior if applicable")
            #     retrieved_proxy = await crud.get_proxy(proxy_id) # Assuming get_proxy exists
            #     self.assertIsNotNone(retrieved_proxy)
            #     self.assertEqual(retrieved_proxy.id, proxy_id)
            #     # Add cache hit/miss checks if get_proxy is cached

    async def test_c2_implants(self):
        async with self.SessionLocal() as db:
            c2_server_to_create = schemas.C2ServerCreate(type="mythic")
            c2_server1 = await crud.create_c2_server(db, c2_server_to_create)

            to_create = schemas.C2ImplantCreate(
                c2_server_id=c2_server1.id, internal_id="test_implant_1"
            )
            created, c2_implants1 = await crud.create_or_update_c2_implant(
                db, to_create
            )
            self.assertTrue(created)
            self.assertIsNotNone(c2_implants1)
            implant1_id = c2_implants1.id

            created, c2_implants2 = await crud.create_or_update_c2_implant(
                db, to_create
            )
            self.assertFalse(created)  # Should update, not create
            self.assertIsNotNone(c2_implants2)
            self.assertEqual(implant1_id, c2_implants2.id)

            filter_list = await crud.get_c2_implant_filters(db, filters.ImplantFilter())
            self.assertGreater(len(filter_list), 0)  # Check it's not empty

    async def test_certificate_authoritys(self):
        async with self.SessionLocal() as db:
            to_create = schemas.CertificateAuthorityCreate(
                ca_name="test_ca", dns_name="test.local"
            )
            created, ca1 = await crud.create_certificate_authority(db, to_create)
            self.assertTrue(created)
            self.assertIsNotNone(ca1)
            ca1_id = ca1.id

            created, ca2 = await crud.create_certificate_authority(db, to_create)
            self.assertFalse(created)  # Not created again
            self.assertIsNotNone(ca2)
            self.assertEqual(ca1_id, ca2.id)

            filter_list = await crud.get_certificate_authorities_filters(
                db, filters.CertificateAuthorityFilter()
            )
            self.assertGreater(len(filter_list), 0)  # Check not empty

    async def test_certificate_templates(self):
        async with self.SessionLocal() as db:
            template_name = f"test_template_{uuid.uuid4()}"
            to_create = schemas.CertificateTemplateCreate(template_name=template_name)
            created, template1 = await crud.create_certificate_template(db, to_create)
            self.assertTrue(created)
            self.assertIsNotNone(template1)
            template1_id = template1.id
            filter_list = await crud.get_certificate_templates_filters(
                db, filters.CertificateTemplateFilter()
            )
            self.assertGreater(len(filter_list), 0)

    async def test_hashs(self):
        async with self.SessionLocal() as db:
            hash_value = f"test_hash_{uuid.uuid4()}"
            to_create = schemas.HashCreate(hash=hash_value, type="test_type")
            created, hash1 = await crud.create_hash(db, to_create)
            self.assertTrue(created)
            self.assertIsNotNone(hash1)
            hash1_id = hash1.id

            created, hash2 = await crud.create_hash(db, to_create)
            self.assertFalse(created)  # Not created again
            self.assertIsNotNone(hash2)
            self.assertEqual(hash1_id, hash2.id)


# --- Allow running the tests directly ---
if __name__ == "__main__":
    unittest.main()
