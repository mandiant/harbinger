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

import uuid

import pytest

# Assume these are your application modules
from harbinger import crud, filters, schemas
from sqlalchemy.ext.asyncio import AsyncSession

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


async def test_domain(db_session: AsyncSession):
    """Tests basic domain creation and retrieval."""
    domain = await crud.get_or_create_domain(db_session, "test")
    domain2 = await crud.get_or_create_domain(db_session, "test")
    assert domain.id is not None
    assert domain2.id is not None
    assert domain.id == domain2.id

    await crud.set_long_name(db_session, domain.id, "test.local")

    # Refresh the object to get the updated value within the same session
    await db_session.refresh(domain)

    assert domain.long_name == "test.local"


async def test_password_creation_and_retrieval(db_session: AsyncSession):
    """Tests that a password can be created and retrieved."""
    password_value = f"test_password_{uuid.uuid4()}"

    # 1. Create the password
    password_obj_1 = await crud.get_or_create_password(
        db_session,
        password=password_value,
    )
    assert password_obj_1.id is not None
    created_password_id = password_obj_1.id

    # 2. Get the password
    password_obj_2 = await crud.get_password(db_session, created_password_id)
    assert password_obj_2 is not None
    assert password_obj_2.id == created_password_id

    # 3. Test get_passwords
    passwords_list = await crud.get_passwords(db_session, password_value)
    assert len(list(passwords_list)) == 1


async def test_proxies(db_session: AsyncSession):
    """Tests proxy creation."""
    proxy = await crud.create_proxy(
        db_session,
        schemas.ProxyCreate(
            port=8080,
            type=schemas.ProxyType.socks5,
            status=schemas.ProxyStatus.connected,
        ),
    )
    assert proxy.id is not None


async def test_c2_implants(db_session: AsyncSession):
    """Tests creation and updating of C2 implants."""
    c2_server_to_create = schemas.C2ServerCreate(type="mythic")
    c2_server1 = await crud.create_c2_server(db_session, c2_server_to_create)

    to_create = schemas.C2ImplantCreate(
        c2_server_id=c2_server1.id,
        internal_id="test_implant_1",
    )
    created, c2_implants1 = await crud.create_or_update_c2_implant(
        db_session,
        to_create,
    )
    assert created
    assert c2_implants1 is not None
    implant1_id = c2_implants1.id

    created, c2_implants2 = await crud.create_or_update_c2_implant(
        db_session,
        to_create,
    )
    assert not created, "Implant should have been updated, not created"
    assert c2_implants2 is not None
    assert implant1_id == c2_implants2.id

    filter_list = await crud.get_c2_implant_filters(db_session, filters.ImplantFilter())
    assert len(filter_list) > 0


async def test_certificate_authorities(db_session: AsyncSession):
    """Tests creation of Certificate Authorities."""
    to_create = schemas.CertificateAuthorityCreate(
        ca_name="test_ca",
        dns_name="test.local",
    )
    created, ca1 = await crud.create_certificate_authority(db_session, to_create)
    assert created
    assert ca1 is not None
    ca1_id = ca1.id

    created, ca2 = await crud.create_certificate_authority(db_session, to_create)
    assert not created, "CA should not be created again"
    assert ca2 is not None
    assert ca1_id == ca2.id

    filter_list = await crud.get_certificate_authorities_filters(
        db_session,
        filters.CertificateAuthorityFilter(),
    )
    assert len(filter_list) > 0


async def test_certificate_templates(db_session: AsyncSession):
    """Tests creation of Certificate Templates."""
    template_name = f"test_template_{uuid.uuid4()}"
    to_create = schemas.CertificateTemplateCreate(template_name=template_name)
    created, template1 = await crud.create_certificate_template(db_session, to_create)
    assert created
    assert template1 is not None

    filter_list = await crud.get_certificate_templates_filters(
        db_session,
        filters.CertificateTemplateFilter(),
    )
    assert len(filter_list) > 0


async def test_hashes(db_session: AsyncSession):
    """Tests creation of Hashes."""
    hash_value = f"test_hash_{uuid.uuid4()}"
    to_create = schemas.HashCreate(hash=hash_value, type="test_type")
    created, hash1 = await crud.create_hash(db_session, to_create)
    assert created
    assert hash1 is not None
    hash1_id = hash1.id

    created, hash2 = await crud.create_hash(db_session, to_create)
    assert not created, "Hash should not be created again"
    assert hash2 is not None
    assert hash1_id == hash2.id
