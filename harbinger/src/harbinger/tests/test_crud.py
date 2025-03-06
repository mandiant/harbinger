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

from testcontainers.postgres import PostgresContainer
from testcontainers.core.utils import inside_container
from alembic.config import Config
from alembic import command
from harbinger.database import crud
import os
import uuid
from pathlib import Path
from harbinger.config import get_settings
from harbinger.database import crud, schemas, filters
from unittest import mock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


here = Path(os.path.dirname(os.path.abspath(__file__)))

class FixedPostgresContainer(PostgresContainer):
    def get_container_host_ip(self) -> str:
        if inside_container() and Path("/run/docker.sock").exists():
            return self.get_docker_client().gateway_ip(self._container.id)
        return super().get_container_host_ip()

import unittest

class TestCrud(unittest.IsolatedAsyncioTestCase):

    def __init__(self, methodName):
        postgres = None
        super().__init__(methodName)

    def setUp(self):
        self.postgres = FixedPostgresContainer("postgres:14", driver='asyncpg')
        self.postgres.start()
        psql_url = self.postgres.get_connection_url()
        print(psql_url)
        os.environ["pg_dsn"] = psql_url
        os.environ["redis_dsn"] = "test"
        os.environ['minio_access_key'] = "test"
        os.environ['minio_secret_key'] = "test"
        os.environ['minio_host'] = 'localhost'
        os.environ['minio_default_bucket'] = 'test'
        os.environ['temporal_host'] = 'localhost'
        get_settings.cache_clear()
        alembic_cfg = Config()
        alembic_cfg.set_main_option('script_location', str(here / '..' / 'alembic'))
        alembic_cfg.set_main_option('sqlalchemy.url', psql_url)
        command.upgrade(alembic_cfg, 'head')

        engine = create_async_engine(psql_url)
        self.SessionLocal = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def test_domain(self):
        with mock.patch("harbinger.database.crud.send_event") as mockdb:
            async with self.SessionLocal() as db:
                domain = await crud.get_or_create_domain(db, "test")
                domain2 = await crud.get_or_create_domain(db, "test")
                self.assertNotEqual(domain.id, None)
                self.assertNotEqual(domain2.id, None)
                self.assertEqual(domain.id, domain2.id)
                self.assertTrue(await crud.set_long_name(db, domain.id, "test.local"))
                domain3  = await crud.get_domain(db, domain.id)
                self.assertNotEqual(domain3, None)
                if domain3:
                    self.assertEqual(domain3.long_name, "test.local")

    async def test_password(self):
         with mock.patch("harbinger.database.crud.send_event") as mockdb:
            async with self.SessionLocal() as db:
                password1 = await crud.get_or_create_password(db, password="test")
                password2 = await crud.get_or_create_password(db, password="test")
                self.assertNotEqual(password1.id, None)
                self.assertNotEqual(password2.id, None)
                self.assertEqual(password1.id, password2.id)
                mockdb.assert_awaited_once()
                passwords = await crud.get_passwords(db, "test")
                self.assertEqual(len(list(passwords)), 1)
                password = await crud.get_password(db, password1.id)
                self.assertNotEqual(password, None)
                if password:
                    self.assertEqual(password.id, password1.id)

    async def test_proxies(self):
         with mock.patch("harbinger.database.crud.send_event") as mockdb:
            async with self.SessionLocal() as db:
                proxy = await crud.create_proxy(db, schemas.ProxyCreate(
                    port=8080,
                    type=schemas.ProxyType.socks5,
                    status=schemas.ProxyStatus.connected,
                ))
                self.assertNotEqual(proxy.id, None)
                mockdb.assert_awaited_once()
            
    async def test_c2_implants(self):
        with mock.patch("harbinger.database.crud.send_event") as mockdb:
            async with self.SessionLocal() as db:
                c2_server_to_create = schemas.C2ServerCreate(type="mythic")
                c2_server1 = await crud.create_c2_server(db, c2_server_to_create)
                to_create = schemas.C2ImplantCreate(c2_server_id=c2_server1.id, internal_id="test")
                created, c2_implants1 = await crud.create_or_update_c2_implant(db, to_create)
                self.assertTrue(created)
                created, c2_implants2 = await crud.create_or_update_c2_implant(db, to_create)
                self.assertFalse(created)
                self.assertEqual(c2_implants1.id, c2_implants2.id)
                filter_list = await crud.get_c2_implant_filters(db, filters.ImplantFilter())
                self.assertGreater(len(filter_list), 2)
                mockdb.assert_awaited()

    async def test_certificate_authoritys(self):
        with mock.patch("harbinger.database.crud.send_event") as mockdb:
            async with self.SessionLocal() as db:
                to_create = schemas.CertificateAuthorityCreate(ca_name="test", dns_name="test.local")
                created, certificate_authorities1 = await crud.create_certificate_authority(db, to_create)
                self.assertTrue(created)
                created, certificate_authorities2 = await crud.create_certificate_authority(db, to_create)
                self.assertFalse(created)
                self.assertEqual(certificate_authorities1.id, certificate_authorities2.id)
                filter_list = await crud.get_certificate_authorities_filters(db, filters.CertificateAuthorityFilter())
                self.assertGreater(len(filter_list), 2)
                mockdb.assert_awaited_once()

    async def test_certificate_templates(self):
        with mock.patch("harbinger.database.crud.send_event") as mockdb:
            async with self.SessionLocal() as db:
                to_create = schemas.CertificateTemplateCreate(template_name="test") # TODO
                created, _ = await crud.create_certificate_template(db, to_create)
                self.assertTrue(created)
                filter_list = await crud.get_certificate_templates_filters(db, filters.CertificateTemplateFilter())
                self.assertGreater(len(filter_list), 2)
                mockdb.assert_awaited_once()

    async def test_hashs(self):
        with mock.patch("harbinger.database.crud.send_event") as mockdb:
            async with self.SessionLocal() as db:
                to_create = schemas.HashCreate(hash="test", type="test") # TODO
                created, hashs1 = await crud.create_hash(db, to_create)
                self.assertTrue(created)
                created, hashs2 = await crud.create_hash(db, to_create)
                self.assertFalse(created)
                self.assertEqual(hashs1.id, hashs2.id)
                mockdb.assert_awaited_once()   

    def tearDown(self):
        self.postgres.stop()
