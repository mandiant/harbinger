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

import gzip
import json
import os.path
import tempfile
import uuid
from abc import ABC, abstractmethod
from asyncio import create_subprocess_exec
from pathlib import Path

import aiofiles
import structlog
from neo4j import AsyncSession as AsyncNeo4jSession
from pydantic import UUID4, TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, schemas
from harbinger.config import get_settings
from harbinger.files.client import download_file, upload_file
from harbinger.graph import crud as graph_crud
from harbinger.worker.files.schemas import CertifyRoot, CertipyJson
from harbinger.worker.utils import merge_db_neo4j_host

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
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        file: schemas.File,
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
                                        db,
                                        nt_hash=nt,
                                    )
                                    cred = await crud.get_or_create_credential(
                                        db,
                                        username,
                                        domain_id,
                                        password.id,
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
                                    if long_name and long_name != domain and not domain_obj.long_name:
                                        log.info(
                                            f"Setting long name of domain_id: {domain_id}",
                                        )
                                        await crud.set_long_name(
                                            db,
                                            str(domain_id),
                                            long_name,
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
                                        db,
                                        password=password,
                                    )
                                    cred = await crud.get_or_create_credential(
                                        db,
                                        username,
                                        None,
                                        password.id,
                                    )

        log.info("Completed pypykatz!")
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
            "pypykatz",
            "lsa",
            "minidump",
            tmpfilename,
            "--json",
            "-o",
            output_json,
        )
        await proc.wait()
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
        log.info(f"Using convertsnapshot to read {tmpfilename}")
        output_name = "bloodhound.tar.gz"
        proc = await create_subprocess_exec(
            "convertsnapshot",
            "-o",
            output_name,
            tmpfilename,
            cwd=tmpdirname,
        )
        code = await proc.wait()
        if code != 0:
            log.warning("convertsnapshot failed to parse this file, is it a snapshot?")
            return []

        async with aiofiles.open(Path(tmpdirname) / output_name, "rb") as f:
            data = await f.read()

        new_id = uuid.uuid4()
        await upload_file(f"worker/{new_id}_bloodhound.tar.gz", data)
        json_file = await crud.add_file(
            db,
            output_name,
            bucket=file.bucket,
            path=f"worker/{new_id}_bloodhound.tar.gz",
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

            if domain.upper() not in FILTERED_DOMAINS and (
                username
                and "dpapi" not in username
                and username != "NL$KM"
                and (password or nt or (key and algo in ["aes128-cts-hmac-sha1-96", "aes256-cts-hmac-sha1-96"]))
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
                        name = f"{cred.username[:-1]}.{cred.domain.long_name}".upper()
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
            if implant and implant.host_id:
                host = await crud.get_host(db, implant.host_id)

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
        log.info("Done.")
        return []


class CertipyJsonParser(BaseFileParser):
    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,  # graph_db is unused in the provided snippet, but kept in signature
        tmpdirname: str,  # tmpdirname is unused, kept in signature
        tmpfilename: str,
        file: schemas.File,  # file is unused, kept in signature
    ) -> list[schemas.File]:  # Return type is list[schemas.File], currently returns []
        log.info("Processing certipy data")
        async with aiofiles.open(tmpfilename, "rb") as f:
            data = await f.read()

        try:
            certipy = CertipyJson.model_validate_json(data)
        except ValidationError as e:
            log.exception(f"Failed to validate main Certipy JSON: {e.errors()}")
            return []  # Cannot proceed

        # --- Certificate Authorities Processing ---
        if certipy.certificate_authorities and certipy.certificate_authorities.root:
            for ca_value in certipy.certificate_authorities.root.values():
                try:
                    ca_create_schema = schemas.CertificateAuthorityCreate(
                        **ca_value.model_dump(),
                    )
                    created, ca_res = await crud.create_certificate_authority(
                        db,
                        ca_create_schema,
                    )
                    if created:
                        log.info(
                            f"Created authority: {ca_res.id} for CA: {ca_value.ca_name}",
                        )
                except Exception as e_ca:
                    log.exception(
                        f"Error processing CA '{getattr(ca_value, 'ca_name', 'Unknown')}': {e_ca}",
                    )

        # --- Certificate Templates Processing ---
        if certipy.certificate_templates and certipy.certificate_templates.root:
            # Corrected iteration for templates
            for (
                template_value
            ) in certipy.certificate_templates.root.values():  # 'template_value' is CertificateTemplate instance
                try:
                    template_create_schema = schemas.CertificateTemplateCreate(
                        **template_value.model_dump(),
                    )
                    created, template_db_obj = await crud.create_certificate_template(
                        db,
                        template_create_schema,
                    )

                    if created:
                        log.info(
                            f"Created template: {template_db_obj.id} for Template: {template_value.template_name}",
                        )
                        permissions_counter = 0

                        # Safely access and process permissions
                        if template_value.permissions:
                            # --- Enrollment Rights ---
                            enroll_perms = template_value.permissions.enrollment_permissions
                            enrollment_rights_list = []
                            if enroll_perms and enroll_perms.enrollment_rights:
                                enrollment_rights_list = enroll_perms.enrollment_rights

                            for principal in enrollment_rights_list:
                                await crud.create_certificate_template_permissions(
                                    db,
                                    schemas.CertificateTemplatePermissionCreate(
                                        certificate_template_id=template_db_obj.id,
                                        principal=principal,
                                        permission="Enroll",
                                        principal_type="display_name"
                                        if not principal.startswith("S-")
                                        else "object_id",
                                    ),
                                )
                                permissions_counter += 1

                            # --- Object Control Permissions ---
                            ocp = template_value.permissions.object_control_permissions
                            if ocp:  # Proceed only if ocp (ObjectControlPermissions object) exists
                                # Owner
                                if ocp.owner:  # ocp.owner is Optional[str]
                                    await crud.create_certificate_template_permissions(
                                        db,
                                        schemas.CertificateTemplatePermissionCreate(
                                            certificate_template_id=template_db_obj.id,
                                            principal=ocp.owner,
                                            principal_type="display_name"
                                            if not ocp.owner.startswith("S-")
                                            else "object_id",
                                            permission="Owner",
                                        ),
                                    )
                                    permissions_counter += 1

                                # Full Control Principals (assuming ocp.full_control_principals is Optional[List[str]])
                                for principal in ocp.full_control_principals or []:
                                    await crud.create_certificate_template_permissions(
                                        db,
                                        schemas.CertificateTemplatePermissionCreate(
                                            certificate_template_id=template_db_obj.id,
                                            principal=principal,
                                            principal_type="display_name"
                                            if not principal.startswith("S-")
                                            else "object_id",
                                            permission="FullControl",
                                        ),
                                    )
                                    permissions_counter += 1

                                # Write Owner Principals
                                for principal in ocp.write_owner_principals or []:
                                    await crud.create_certificate_template_permissions(
                                        db,
                                        schemas.CertificateTemplatePermissionCreate(
                                            certificate_template_id=template_db_obj.id,
                                            principal=principal,
                                            principal_type="display_name"
                                            if not principal.startswith("S-")
                                            else "object_id",
                                            permission="WriteOwner",
                                        ),
                                    )
                                    permissions_counter += 1

                                # Write Dacl Principals
                                for principal in ocp.write_dacl_principals or []:
                                    await crud.create_certificate_template_permissions(
                                        db,
                                        schemas.CertificateTemplatePermissionCreate(
                                            certificate_template_id=template_db_obj.id,
                                            principal=principal,
                                            principal_type="display_name"
                                            if not principal.startswith("S-")
                                            else "object_id",
                                            permission="WriteDacl",
                                        ),
                                    )
                                    permissions_counter += 1

                                # Write Property Principals
                                # Safely access 'write_property_principals'.
                                # Ensure this field exists in your ObjectControlPermissions Pydantic model as Optional[List[str]].
                                write_property_principals_list = getattr(ocp, "write_property_principals", None) or []
                                for principal in write_property_principals_list:
                                    await crud.create_certificate_template_permissions(
                                        db,
                                        schemas.CertificateTemplatePermissionCreate(
                                            certificate_template_id=template_db_obj.id,
                                            principal=principal,
                                            principal_type="display_name"
                                            if not principal.startswith("S-")
                                            else "object_id",
                                            permission="WriteProperty",
                                        ),
                                    )
                                    permissions_counter += 1
                        # --- End of Permissions block (if template_value.permissions:) ---

                        # --- Vulnerabilities ---
                        if (
                            template_value.vulnerabilities and template_value.vulnerabilities.root
                        ):  # Safely access .root
                            for name in template_value.vulnerabilities.root:
                                label = await crud.get_label_by_name(
                                    db,
                                    name,
                                )  # Use 'name' (vulnerability key like ESC1) as label name
                                if not label:
                                    label = await crud.create_label(
                                        db,
                                        schemas.LabelCreate(  # Using 'name' for label name, 'vuln_description' could be label's description
                                            name=name,
                                            category="Certificates",
                                            # Consider adding: description=vuln_description, if your LabelCreate supports it
                                        ),
                                    )
                                await crud.create_label_item(
                                    db,
                                    schemas.LabeledItemCreate(
                                        label_id=label.id,
                                        certificate_template_id=template_db_obj.id,
                                    ),
                                )
                        # --- End of Vulnerabilities ---

                        log.info(
                            f"Processed {permissions_counter} permissions for template: {template_db_obj.id}",
                        )
                    # else: (handle if template not created)
                    #    log.warning(f"Template {template_value.template_name} not created. Skipping permissions and vulnerabilities.")

                except Exception as e_template:
                    template_name_for_log = getattr(
                        template_value,
                        "template_name",
                        "Unknown Template",
                    )
                    log.exception(
                        f"Error processing template '{template_name_for_log}': {e_template}",
                    )

        return []  # Original return


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

        template_id_map: dict[str, UUID4] = {}
        template_authority_map: dict[str, UUID4] = {}
        authority_template_map: dict[str, list[str]] = {}
        for entry in stuff:
            if entry.meta.type == "certificateauthorities" and entry.certificate_authorities:
                for authority in entry.certificate_authorities:
                    authority_template_map[authority.ca_name] = authority.templates
                    resp = schemas.CertificateAuthorityCreate(**authority.model_dump())
                    created, auth_db = await crud.create_certificate_authority(db, resp)
                    template_authority_map[authority.ca_name] = auth_db.id
                    if created:
                        log.info(f"Created authority with id: {auth_db.id}")
            elif entry.meta.type == "certificatetemplates" and entry.certificate_templates:
                for template in entry.certificate_templates:
                    cert_template = schemas.CertificateTemplateCreate(
                        **template.model_dump(),
                    )
                    created, templ_db = await crud.create_certificate_template(
                        db,
                        cert_template,
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
                                    principal_type="display_name"
                                    if not template.acl.owner.startswith("S-")
                                    else "object_id",
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
                                                principal_type="display_name"
                                                if not ace.principal.startswith("S-")
                                                else "object_id",
                                                permission="WriteProperty",
                                            ),
                                        )

        for ca, templates in authority_template_map.items():
            for template in templates:
                await crud.create_certificate_authority_map(
                    db,
                    template_authority_map[ca],
                    template_id_map[template],
                )

        return []
