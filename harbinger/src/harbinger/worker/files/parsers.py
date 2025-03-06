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

import asyncio
import json
import os.path
import tempfile
from abc import ABC, abstractmethod
from asyncio import create_subprocess_exec

import aiofiles
from harbinger.config import get_settings
from harbinger.database import crud, models, schemas
from harbinger.files.client import download_file, upload_file
from harbinger.graph import crud as graph_crud
from harbinger.worker.utils import merge_db_neo4j_host

from neo4j import AsyncSession as AsyncNeo4jSession
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import uuid
import structlog
import gzip
from harbinger.worker.files.schemas import CertipyJson, CertifyRoot
from pydantic import TypeAdapter, UUID4

log = structlog.get_logger()

settings = get_settings()

FILTERED_DOMAINS = [
    "FONT DRIVER HOST",
    "WINDOW MANAGER",
    "IIS APPPOOL",
    "NT AUTHORITY",
    "NT SERVICE",
]


class BaseFileParser(ABC):
    """Base fileparser"""

    @abstractmethod
    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        tmpdirname: str,
        tmpfilename: str,
        file: schemas.File,
    ) -> list[schemas.File]:
        return []

    async def base_parse(
        self, db: AsyncSession, graph_db: AsyncNeo4jSession, file: schemas.File
    ) -> list[schemas.File]:
        with tempfile.TemporaryDirectory() as tmpdirname:
            path = os.path.join(tmpdirname, file.filename)
            async with aiofiles.open(path, "wb") as f:
                data = await download_file(file.path)
                await f.write(data)
            log.info(f"{file.filename} downloaded file to {path}")
            return await self.parse(db, graph_db, tmpdirname, path, file)


class PyPyKatzParser(BaseFileParser):
    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        tmpdirname: str,
        tmpfilename: str,
        file: schemas.File,
    ) -> list[schemas.File]:
        log.info(f"Parsing pypykatz json: {tmpfilename}")

        async with aiofiles.open(tmpfilename, "rb") as f:
            data = json.loads(await f.read())

        for y in data.values():
            for value in y["logon_sessions"].values():
                domain = value["domainname"]
                if domain.upper() not in FILTERED_DOMAINS:
                    domain_obj = await crud.get_or_create_domain(db, domain)
                    domain_id = domain_obj.id
                    username = value["username"]
                    if username:
                        # log.info(key, domain, username)
                        if value["msv_creds"]:
                            for cred in value["msv_creds"]:
                                if cred["NThash"]:
                                    nt = cred["NThash"]
                                    password = await crud.get_or_create_password(
                                        db, nt_hash=nt
                                    )
                                    cred = await crud.get_or_create_credential(
                                        db, username, domain_id, password.id
                                    )
                                    log.info(f"Added Credential with id: {cred.id}")
                                    name = f"{cred.username}@{cred.domain.long_name}".upper()
                                    marked = await graph_crud.mark_owned(graph_db, name)
                                    if marked:
                                        log.info(f"Marked {name} as owned in neo4j.")

                        if value["kerberos_creds"]:
                            for kerb in value["kerberos_creds"]:
                                if "domainname" in kerb:
                                    long_name = kerb["domainname"]
                                    if (
                                        long_name
                                        and long_name != domain
                                        and not domain_obj.long_name
                                    ):
                                        log.info(
                                            f"Setting long name of domain_id: {domain_id}"
                                        )
                                        await crud.set_long_name(
                                            db, str(domain_id), long_name
                                        )

                        if value["credman_creds"]:
                            for cred in value["credman_creds"]:
                                password = cred.get("password", "")
                                username = cred.get("username", "")
                                domainname = cred.get("domainname", "")
                                if not username and "@" in domainname:
                                    username = domainname.split(":")[-1]
                                if username and password and username != "teams":
                                    password = await crud.get_or_create_password(
                                        db, password=password
                                    )
                                    cred = await crud.get_or_create_credential(
                                        db, username, None, password.id
                                    )

        log.info(f"Completed pypykatz!")
        return []


class LsassParser(BaseFileParser):
    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        tmpdirname: str,
        tmpfilename: str,
        file: schemas.File,
    ) -> list[schemas.File]:
        log.info(f"Using pypykatz to read {tmpfilename}")
        output_json = f"{tmpfilename}.json"
        proc = await create_subprocess_exec(
            "pypykatz", "lsa", "minidump", tmpfilename, "--json", "-o", output_json
        )
        code = await proc.wait()
        log.info(f"written output to {output_json}")

        async with aiofiles.open(output_json, "rb") as f:
            data = await f.read()

        new_id = uuid.uuid4()
        await upload_file(f"worker/{new_id}_pypykatz.json", data)
        json_file = await crud.add_file(
            db,
            "pypykatz.json",
            bucket=file.bucket,
            path=f"worker/{new_id}_pypykatz.json",
            id=new_id,
            c2_implant_id=file.c2_implant_id,
            c2_task_id=file.c2_task_id,
            filetype=schemas.FileType.pypykatz_json,
        )
        return [schemas.File.model_validate(json_file)]


class NanoDumpParser(LsassParser):
    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        tmpdirname: str,
        tmpfilename: str,
        file: schemas.File,
    ) -> list[schemas.File]:
        async with aiofiles.open(tmpfilename, "r+b") as f:
            await f.write(b"\x4d\x44\x4d\x50\x93\xa7\x00\x00")

        return await super().parse(db, graph_db, tmpdirname, tmpfilename, file)


class ADSnapshotParser(BaseFileParser):
    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        tmpdirname: str,
        tmpfilename: str,
        file: schemas.File,
    ) -> list[schemas.File]:
        log.info(f"Using ADExplorerSnapshot.py to read {tmpfilename}")
        proc = await create_subprocess_exec(
            "ADExplorerSnapshot.py", "-o", "output", tmpfilename, cwd=tmpdirname
        )
        code = await proc.wait()
        if code != 0:
            log.warning(
                "ADExplorerSnapshot.py failed to parse this file, is it a snapshot?"
            )
            return []

        output_name = f"{tmpfilename}.zip"
        output_dir = os.path.join(tmpdirname, "output")

        proc3 = await create_subprocess_exec(
            "ls", "-1", output_dir, stdout=asyncio.subprocess.PIPE
        )
        lines = await proc3.communicate()
        include = []
        for line in lines[0].decode("utf-8").split("\n"):
            include.append(os.path.join(output_dir, line))
        proc2 = await create_subprocess_exec(
            "zip", "-j", output_name, *include, cwd=tmpdirname
        )
        code = await proc2.wait()
        if code != 0:
            raise ValueError("Unable to zip result files.")

        log.info(f"Writing results to {output_name}")

        async with aiofiles.open(output_name, "rb") as f:
            data = await f.read()

        new_id = uuid.uuid4()
        await upload_file(f"worker/{new_id}_bloodhound.zip", data)
        json_file = await crud.add_file(
            db,
            "BloodHound.zip",
            bucket=file.bucket,
            path=f"worker/{new_id}_bloodhound.zip",
            id=new_id,
            c2_implant_id=file.c2_implant_id,
            c2_task_id=file.c2_task_id,
            filetype=schemas.FileType.bloodhound_zip,
        )
        return [schemas.File.model_validate(json_file)]


class SecretsDumpParser(BaseFileParser):
    """Parses secretsdump"""

    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        tmpdirname: str,
        tmpfilename: str,
        file: schemas.File,
    ) -> list[schemas.File]:
        log.info(f"Parsing secretsdump: {tmpfilename} which is a {file.filename}")
        # await super().parse(db, graph_db, tmpdirname, tmpfilename, file)

        async with aiofiles.open(tmpfilename) as f:
            lines = await f.readlines()

        for line in lines:
            line = line.strip()
            domain = ""
            username = ""
            password = ""
            lm = ""
            nt = ""
            algo = ""
            key = ""
            if "\\" in line:
                domain, line = line.split("\\", 1)
            count = line.count(":")
            if count == 1:
                username, password = line.split(":", 1)
            if count == 2:
                username, algo, key = line.split(":")
            if count == 5:
                username, lm, nt, *remainder = line.split(":")
            if count == 6:
                username, _, lm, nt, *remainder = line.split(":")

            if domain.upper() not in FILTERED_DOMAINS:
                if (
                    username
                    and "dpapi" not in username
                    and username != "NL$KM"
                    and (
                        password
                        or nt
                        or (
                            key
                            and algo
                            in ["aes128-cts-hmac-sha1-96", "aes256-cts-hmac-sha1-96"]
                        )
                    )
                ):
                    domain_obj = await crud.get_or_create_domain(db, domain)
                    password = await crud.get_or_create_password(
                        db=db,
                        password=password,
                        nt_hash=nt,
                        aes128_key=key if algo == "aes128-cts-hmac-sha1-96" else "",
                        aes256_key=key if algo == "aes256-cts-hmac-sha1-96" else "",
                    )
                    cred = await crud.get_or_create_credential(
                        db,
                        username=username,
                        domain_id=domain_obj.id,
                        password_id=password.id,
                    )
                    name = ""
                    if cred.domain and cred.domain.long_name:
                        if username.endswith("$"):
                            name = (
                                f"{cred.username[:-1]}.{cred.domain.long_name}".upper()
                            )
                        else:
                            name = f"{cred.username}@{cred.domain.long_name}".upper()
                        marked = await graph_crud.mark_owned(graph_db, name)
                        if marked:
                            log.info(f"Marked {name} as owned in neo4j.")
        log.info(f"Completed {tmpfilename}")
        return []


class ProcessListParser(BaseFileParser):
    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        tmpdirname: str,
        tmpfilename: str,
        file: schemas.File,
    ) -> list[schemas.File]:
        async with aiofiles.open(tmpfilename, "rb") as f:
            data = json.loads(await f.read())

        target = data["target"]
        created, host = await crud.get_or_create_host(db, target)

        number = await crud.get_highest_process_number(db, host.id)

        for process in data["data"]:
            stuff = schemas.ProcessCreate(**process)
            stuff.host_id = host.id
            stuff.number = number + 1
            await crud.create_process(db, stuff)

        # await label_processes({}, str(host.id), number + 1)

        if created and host.domain_id:
            domain = await crud.get_domain(db, host.domain_id)
            if domain:
                await merge_db_neo4j_host(db, host, domain, False)
        return []


class Dir2JsonParser(BaseFileParser):
    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        tmpdirname: str,
        tmpfilename: str,
        file: schemas.File,
    ) -> list[schemas.File]:
        host = ""
        domain = ""
        if file.c2_implant_id:
            implant = await crud.get_c2_implant(db, file.c2_implant_id)
            if implant:
                host_db = await crud.get_host(db, implant.host_id)
                if host_db:
                    host = host_db.name
                    if host_db.fqdn:
                        host = host_db.fqdn
                    elif host_db.domain_id:
                        domain = await crud.get_domain_name_from_host(db, host_db.id)

        async with aiofiles.open(tmpfilename, "rb") as f:
            data = await f.read()

        data_json = json.loads(gzip.decompress(data))
        parsed = schemas.Dir2JsonShareFile(**data_json)

        try:
            parsed.parse(host, domain)
            _, file_db = await crud.save_parsed_share_file(db, parsed)
            log.info(f"Created file with id: {file_db.id}")
        except ValueError:
            log.warning("Unable to correctly parse dir2json file.")
        log.info(f"Done.")
        return []


class CertipyJsonParser(BaseFileParser):
    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        tmpdirname: str,
        tmpfilename: str,
        file: schemas.File,
    ) -> list[schemas.File]:
        log.info("Processing certipy data")
        async with aiofiles.open(tmpfilename, "rb") as f:
            data = await f.read()
        certipy = CertipyJson.model_validate_json(data)
        for auth in certipy.certificate_authorities:
            for value in auth[1].values():
                created, res = await crud.create_certificate_authority(
                    db, schemas.CertificateAuthorityCreate(**value.model_dump())
                )
                if created:
                    log.info(f"Created authority: {res.id}")
        for entry in certipy.certificate_templates:
            for value in entry[1].values():
                created, res = await crud.create_certificate_template(
                    db, schemas.CertificateTemplateCreate(**value.model_dump())
                )
                permissions = 0
                for principal in (
                    value.permissions.enrollment_permissions.enrollment_rights or []
                ):
                    await crud.create_certificate_template_permissions(
                        db,
                        schemas.CertificateTemplatePermissionCreate(
                            certificate_template_id=res.id,
                            principal=principal,
                            permission="Enroll",
                            principal_type="display_name" if not principal.startswith("S-") else "object_id",
                        ),
                    )
                    permissions += 1

                if value.permissions.object_control_permissions.owner:
                    await crud.create_certificate_template_permissions(
                        db,
                        schemas.CertificateTemplatePermissionCreate(
                            certificate_template_id=res.id,
                            principal=value.permissions.object_control_permissions.owner,
                            principal_type="display_name" if not value.permissions.object_control_permissions.owner.startswith("S-") else "object_id",
                            permission="Owner",
                        ),
                    )
                    permissions += 1

                for principal in (
                    value.permissions.object_control_permissions.full_control_principals
                    or []
                ):
                    await crud.create_certificate_template_permissions(
                        db,
                        schemas.CertificateTemplatePermissionCreate(
                            certificate_template_id=res.id,
                            principal=principal,
                            principal_type="display_name" if not principal.startswith("S-") else "object_id",
                            permission="FullControl",
                        ),
                    )
                    permissions += 1

                for principal in (
                    value.permissions.object_control_permissions.write_owner_principals
                    or []
                ):
                    await crud.create_certificate_template_permissions(
                        db,
                        schemas.CertificateTemplatePermissionCreate(
                            certificate_template_id=res.id,
                            principal=principal,
                            principal_type="display_name" if not principal.startswith("S-") else "object_id",
                            permission="WriteOwner",
                        ),
                    )
                    permissions += 1

                for principal in (
                    value.permissions.object_control_permissions.write_dacl_principals
                    or []
                ):
                    await crud.create_certificate_template_permissions(
                        db,
                        schemas.CertificateTemplatePermissionCreate(
                            certificate_template_id=res.id,
                            principal=principal,
                            principal_type="display_name" if not principal.startswith("S-") else "object_id",
                            permission="WriteDacl",
                        ),
                    )
                    permissions += 1

                for principal in (
                    value.permissions.object_control_permissions.write_property_principals
                    or []
                ):
                    await crud.create_certificate_template_permissions(
                        db,
                        schemas.CertificateTemplatePermissionCreate(
                            certificate_template_id=res.id,
                            principal=principal,
                            principal_type="display_name" if not principal.startswith("S-") else "object_id",
                            permission="WriteProperty",
                        ),
                    )
                    permissions += 1
                if value.vulnerabilities:
                    for name, entry in value.vulnerabilities.root.items():
                        label = await crud.get_label_by_name(db, name)
                        if not label:
                            label = await crud.create_label(
                                db,
                                schemas.LabelCreate(
                                    name=entry, category="Certificates",  # type: ignore
                                ),
                            )
                        await crud.create_label_item(
                            db,
                            schemas.LabeledItemCreate(
                                label_id=label.id,
                                certificate_template_id=res.id,
                            ),
                        )
                if created:
                    log.info(f"Created template: {res.id} with {permissions} permissions")
        return []


class CertifyJsonParser(BaseFileParser):
    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        tmpdirname: str,
        tmpfilename: str,
        file: schemas.File,
    ) -> list[schemas.File]:
        log.info("Processing certify data")
        async with aiofiles.open(tmpfilename, "rb") as f:
            data = await f.read()

        ta = TypeAdapter(list[CertifyRoot])
        stuff = ta.validate_json(data)

        template_id_map: dict[str, UUID4] = dict()
        template_authority_map: dict[str, UUID4] = dict()
        authority_template_map: dict[str, list[str]] = dict()
        for entry in stuff:
            if entry.meta.type == 'certificateauthorities' and entry.certificate_authorities:
                for authority in entry.certificate_authorities:
                    authority_template_map[authority.ca_name] = authority.templates
                    resp = schemas.CertificateAuthorityCreate(**authority.model_dump())
                    created, auth_db = await crud.create_certificate_authority(
                        db, resp
                    )
                    template_authority_map[authority.ca_name] = auth_db.id
                    if created:
                        log.info(f"Created authority with id: {auth_db.id}")
            elif entry.meta.type == 'certificatetemplates' and entry.certificate_templates:
                for template in entry.certificate_templates:
                    cert_template = schemas.CertificateTemplateCreate(**template.model_dump())
                    created, templ_db = await crud.create_certificate_template(
                        db, cert_template
                    )
                    template_id_map[template.template_name] = templ_db.id
                    if created:
                        log.info(f"Created template with id: {templ_db.id}")
                    if template.acl:
                        for ace in template.acl.aces:
                            await crud.create_certificate_template_permissions(
                                db,
                                schemas.CertificateTemplatePermissionCreate(
                                    certificate_template_id=templ_db.id,
                                    principal=template.acl.owner,
                                    permission="Enroll",
                                    principal_type="display_name" if not template.acl.owner.startswith("S-") else "object_id",
                                ),
                            )
                            if ace.type == "Allow":
                                rights = ace.rights.split(", ")
                                for right in rights:
                                    if right:
                                        await crud.create_certificate_template_permissions(
                                            db,
                                            schemas.CertificateTemplatePermissionCreate(
                                                certificate_template_id=templ_db.id,
                                                principal=ace.principal,
                                                principal_type="display_name" if not ace.principal.startswith("S-") else "object_id",
                                                permission="WriteProperty",
                                            ),
                                        )

        for ca, templates in authority_template_map.items():
            for template in templates:
                await crud.create_certificate_authority_map(db, template_authority_map[ca], template_id_map[template])

        return []
