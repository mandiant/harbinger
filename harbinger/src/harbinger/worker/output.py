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

from asyncio import create_subprocess_exec
import asyncio
import base64
import json
import uuid
from harbinger.worker.client import get_client
from pyasn1.codec.ber import decoder
from impacket.krb5.asn1 import AP_REQ
import re
import abc
import struct
import ipaddress
import aiofiles
from pathlib import Path

from base64 import b64decode, b64encode
from impacket.krb5.ccache import CCache
from sqlalchemy.ext.asyncio import AsyncSession
from harbinger.database import crud, schemas
from datetime import datetime
import structlog
from pydantic import UUID4, TypeAdapter
from harbinger.config import get_settings
from harbinger.files.client import upload_file
from pydantic_core import ValidationError
from harbinger.config import constants
from harbinger.graph.database import get_async_neo4j_session_context
from harbinger.graph import crud as graph_crud
from harbinger.worker import genai


log = structlog.get_logger()
settings = get_settings()


class OutputParser(abc.ABC):
    needle: list[str] = []
    labels: list[str] = []

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @abc.abstractmethod
    async def match(self, text: str) -> bool:
        raise NotImplementedError("This should be implemented")

    @abc.abstractmethod
    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        raise NotImplementedError("This should be implemented")

    async def process_file(self, file_id: str) -> None:
        from harbinger.worker.workflows import ParseFile

        client = await get_client()
        await client.start_workflow(
            ParseFile.run,
            file_id,
            id=str(uuid.uuid4()),
            task_queue=constants.FILE_PROCESSING_TASK_QUEUE,
        )


class SimpleMatchParser(OutputParser):
    """Checks if needle is in the output."""

    async def match(
        self,
        text: str,
    ) -> bool:
        for needle in self.needle:
            if needle in text:
                return True
        return False


class RegexMatchParser(OutputParser):
    """Checks if need is in the output by using a regex"""

    async def match(
        self,
        text: str,
    ) -> bool:
        for needle in self.needle:
            regex = re.findall(needle, text)
            if regex:
                return True
        return False


# class CommandMatchParser(OutputParser):
#     """Checks if the needle is in the command name."""

#     async def match(
#         self, text: str, c2_implant_id: str | UUID4 | None = None
#     ) -> bool:
#         if c2_task:
#             for needle in self.needle:
#                 if needle in c2_task.command_name:
#                     return True
#         return False


# class DisplayParamsMatchParser(OutputParser):
#     """Checks if the needle is in the display params."""

#     async def match(
#         self, text: str, c2_implant_id: str | UUID4 | None = None
#     ) -> bool:
#         if c2_task:
#             for needle in self.needle:
#                 if needle in c2_task.display_params:
#                     return True
#         return False


async def parse_ccache(db: AsyncSession, ticket: bytes):
    try:
        ccache = CCache(ticket)
    except struct.error:
        ccache = CCache()
        ccache.fromKRBCRED(ticket)

    kirbi_data = ccache.toKRBCRED()
    ccache_data = ccache.getData()

    if ccache.credentials:
        cred = ccache.credentials[0]
        clientname = cred.header["client"].prettyPrint().decode("utf-8")
        server = cred.header["server"].prettyPrint().decode("utf-8")
        key = cred.header["key"].prettyPrint()
        if key[8:10] == "12":
            keytype = "AES256"
        elif key[8:10] == "17":
            keytype = "RC4"
        elif key[8:10] == "11":
            keytype = "AES128"
        elif key[8:10] == "0x1)" or key[8:10] == "0x3)":
            keytype = "DES"
        else:
            log.info(f"Unknown ticket type")
        times = cred.header["time"]
        kerb_cred = schemas.KerberosCreate(
            client=clientname,
            server=server,
            key=key,
            keytype=keytype,
            ccache=b64encode(ccache_data).decode("utf-8"),
            kirbi=b64encode(kirbi_data).decode("utf-8"),
            auth=datetime.fromtimestamp(times["authtime"]),
            start=datetime.fromtimestamp(times["starttime"]),
            end=datetime.fromtimestamp(times["endtime"]),
            renew=datetime.fromtimestamp(times["renew_till"]),
        )
        created, kerb_obj = await crud.get_or_create_kerberos(db, kerb_cred)
        if created:
            log.info(f"Created new kerberos object: {kerb_obj.id}")
            username, domain = clientname.split("@", 1)
            domain_obj = await crud.get_or_create_domain(db, domain)
            cred = await crud.get_or_create_credential(
                db, username, domain_obj.id, kerberos_id=kerb_obj.id
            )
            log.info(f"Created new credential: {cred.id}")
    else:
        log.warning("No credentials found in ccache.")


class KirbiParser(SimpleMatchParser):
    needle = ["[*] base64(ticket.kirbi):"]
    labels = ["4bf0c79a-6994-4324-9cf6-0dfef6e37551"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        ticket = ""
        needle_offset = text.find(self.needle[0])
        data = text[needle_offset:]
        for entry in data.splitlines():
            if entry.startswith("["):
                continue
            if not entry:
                continue
            ticket = entry
            break

        if not ticket:
            log.warning("[KirbiParser] Unable to retrieve the ticket from the output.")
            return

        try:
            ticket_decoded = b64decode(ticket)
            await parse_ccache(self.db, ticket_decoded)
        except Exception as e:
            log.error(f"Exception parsing ticket: {e}")


class EnvParser(SimpleMatchParser):
    needle = ["Gathering Process Environment Variables:"]
    labels = ["f198bd07-16ee-4fea-954b-5dad3bfb8455"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        env_vars = dict()
        for entry in text.splitlines():
            if entry.count("=") == 1:
                key, value = entry.split("=")
                env_vars[key] = value

        computername = env_vars.get("COMPUTERNAME", "")
        userdomain = env_vars.get("USERDOMAIN", "")
        userdomain_long = env_vars.get("USERDNSDOMAIN", "")
        logon_server = env_vars.get("LOGONSERVER", "")

        if computername and computername != userdomain:
            log.info("Computer is domain joined.")

            if not c2_implant_id:
                return

            implant = await crud.get_c2_implant(c2_implant_id)
            if implant and implant.domain != userdomain:
                implant = await crud.update_c2_implant(
                    self.db,
                    c2_implant_id=c2_implant_id,
                    implant=schemas.C2ImplantUpdate(domain=userdomain),
                )

            domain = await crud.get_or_create_domain(self.db, userdomain)
            if (
                domain
                and userdomain_long
                and userdomain_long != userdomain
                and not domain.long_name
            ):
                log.info(f"Setting long name of domain to {userdomain_long}")
                await crud.set_long_name(
                    self.db, domain_id=domain.id, long_name=userdomain_long
                )

            await self.db.refresh(implant)
            if implant and implant.host_id:
                host = await crud.get_host(implant.host_id)
                if host and not host.domain_id:
                    log.info("Domain not set on this host, setting now.")
                    host = await crud.update_host(
                        self.db, host.id, schemas.HostBase(domain_id=domain.id)
                    )
            logon_server = logon_server.replace("\\", "")
            if logon_server != computername and logon_server:
                log.info(f"Found a logon server: {logon_server}")
                await crud.get_or_create_situational_awareness(
                    self.db,
                    sa=schemas.SituationalAwarenessCreate(
                        name=schemas.SANames.domain_controller,
                        category=schemas.SACategories.domain,
                        value_string=logon_server,
                        domain_id=domain.id,
                    ),
                )


class IPConfigParser(SimpleMatchParser):
    needle = ["DNS Server: 	"]
    labels = ["40bcc903-5b4c-4aef-9ba3-f0d1fc61d4c0"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        offset = text.find(self.needle[0])
        for line in text[offset:].splitlines():
            address = line.split("\t")[-1]
            try:
                ip = ipaddress.ip_address(address)
            except ValueError:
                continue
            if ip.is_private and not ip.is_loopback:
                log.info(f"Found a dns server ip: {ip}")
                await crud.get_or_create_situational_awareness(
                    self.db,
                    sa=schemas.SituationalAwarenessCreate(
                        name=schemas.SANames.dns_server_ip,
                        category=schemas.SACategories.domain,
                        value_string=str(ip),
                    ),
                )


class WhoamiParser(SimpleMatchParser):
    needle = ["GROUP INFORMATION"]
    labels = ["1343ada1-b187-44d5-bfd0-612e32af46c6"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        pass


class SnafflerParser(SimpleMatchParser):
    needle = [
        " [Share] {Green}<",
        " [File] {Red}",
        " [File] {Green}",
        " [File] {Yellow}",
    ]
    labels = ["3560c81d-bd0b-4636-9d03-3918e630ffb9"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        pattern = re.compile(r"\[Share\] {Green}<(.*)>\(?.\) ?(.*)")

        label_map = {
            "Green": "9a36716a-e41c-4398-a121-4611625c148f",
            "Yellow": "a2e41186-15bb-4748-86ec-511e66dcb7dd",
            "Red": "56c57825-1c46-4113-8f89-14c40c8624f0",
        }

        for share, description in pattern.findall(text):
            domain = ""
            try:
                hostname, sharename = [x for x in share.split("\\") if x]
            except ValueError:
                log.warning(f"ValueError on {share}")
                continue

            if "." in hostname:
                hostname, domain = hostname.split(".", 1)
            domain_id = None
            if domain:
                d = await crud.get_or_create_domain(self.db, domain)
                domain_id = d.id

            _, h = await crud.get_or_create_host(self.db, hostname, domain_id)
            host_id = h.id

            created, share_db = await crud.get_or_create_share(
                self.db,
                schemas.ShareCreate(
                    host_id=host_id,
                    name=sharename,
                    unc_path=share,
                    remark=description,
                ),
            )
            if created:
                log.info(
                    f"Created new share with name: {share_db.unc_path} ({share_db.id})"
                )

        pattern = re.compile(r"\[File\] {(.*)}<.*>\((.*)\) .*")

        for color, path in pattern.findall(text):
            p = schemas.BaseParsedShareFile(name=path)
            p.parse("", "", False)
            p.type = "file"
            _, sharefile = await crud.save_parsed_share_file(self.db, p)

            label_id = label_map.get(color, None)
            if label_id:
                await crud.create_label_item(
                    self.db,
                    schemas.LabeledItemCreate(
                        label_id=label_id,
                        share_file_id=sharefile.id,
                    ),
                )
        await self.db.commit()


class KerberosHashParser(RegexMatchParser):
    needle = [r"(\$krb5tgs\$[0-9]{2}\$[^$]*\$[^$]*\$[^$]*\$[^$]*\$[a-fA-F0-9]*)"]
    labels = ["823afdbb-ef49-4cc1-9368-4e125606649c"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        for n in self.needle:
            tester = re.compile(n)
            for hit in tester.findall(text):
                _, _, etype, username, domain, spn, _, _ = hit.split("$", 7)

                hash_type = ""
                hashcat_id = 0

                if int(etype) == 23:
                    hashcat_id = 13100
                    hash_type = "krb5tgs-etype23-rc4"
                elif int(etype) == 17:
                    hashcat_id = 19600
                    hash_type = "krb5tgs-etype17-aes128"
                elif int(etype) == 18:
                    hashcat_id = 19700
                    hash_type = "krb5tgs-etype18-aes256"

                created, hash_db = await crud.create_hash(
                    self.db,
                    schemas.HashCreate(
                        type=hash_type,
                        hashcat_id=hashcat_id,
                        hash=hit.replace('\x00', ''),
                    ),
                )
                if created:
                    log.info(
                        f"Created new hash with id: {hash_db.id} from user: {username}@{domain} with spn: {spn}"
                    )


class ASREPRoastingHashParser(RegexMatchParser):
    needle = [r"(\$krb5asrep\$[^$]*@[^:]*:[^$]*\$[a-fA-F0-9]*)"] 
    labels = ["b360fffa-ef10-46aa-ba0b-056cf7405b8a"] 

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        for n in self.needle:
            tester = re.compile(n)
            for hit in tester.findall(text):
                await crud.create_hash(
                    self.db,
                    schemas.HashCreate(
                        type="krb5asrep",  
                        hashcat_id=18200,  
                        hash=hit.replace('\x00', ''), 
                    ),
                )


class BofRoastParser(SimpleMatchParser):
    needle = ["Got Ticket! Convert it with apreq2hashcat.py"]
    labels = ["4bf0c79a-6994-4324-9cf6-0dfef6e37551"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        location = text.find("apreq2hashcat.py")
        if location == -1:
            return
        base64_encoded = text[location + len("apreq2hashcat.py") :]
        # from https://raw.githubusercontent.com/cube0x0/BofRoast/main/BofRoast/apreq2hashcat.py
        fd = base64.b64decode(base64_encoded)
        i = 0
        while fd[i] != 0x6E:
            i += 1
        ap_req = decoder.decode(fd[i:], asn1Spec=AP_REQ())[0]
        service = ap_req["ticket"]["sname"]["name-string"][0]._value
        host = ap_req["ticket"]["sname"]["name-string"][1]._value
        domain = ap_req["ticket"]["realm"]._value
        encType = ap_req["ticket"]["enc-part"]["etype"]._value
        hash = (
            ap_req["ticket"]["enc-part"]["cipher"]._value[:16].hex().upper()
            + "$"
            + ap_req["ticket"]["enc-part"]["cipher"]._value[16:].hex().upper()
        )

        if int(encType) == 23:
            hashcat_id = 13100
            hash_type = "krb5tgs-etype23-rc4"
        elif int(encType) == 17:
            hashcat_id = 19600
            hash_type = "krb5tgs-etype17-aes128"
        elif int(encType) == 18:
            hashcat_id = 19700
            hash_type = "krb5tgs-etype18-aes256"

        created, hash_db = await crud.create_hash(
            self.db,
            schemas.HashCreate(
                type=hash_type,
                hashcat_id=hashcat_id,
                hash="$krb5tgs${0}$*{1}${2}${1}/{3}@{2}*${4}".format(
                    encType, service, domain, host, hash
                ),
            ),
        )
        if created:
            log.info(
                f"Created new hash with id: {hash_db.id} from user: {service}@{domain} with spn: {host}"
            )


class LdapSearchParser(SimpleMatchParser):
    needle = ["[*] Distinguished name: "]
    labels = ["9f30b8d6-5d30-492c-8856-c53465122e8f"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        async with aiofiles.tempfile.TemporaryDirectory() as dir:
            d = Path(dir)
            async with aiofiles.open(d / "input", "w") as f:
                await f.write(text)

            proc = await create_subprocess_exec(
                settings.bofhound, "--input", d / "input", "--output", dir
            )

            await proc.wait()
            log.info(f"written output to {dir}")

            for entry in d.iterdir():
                if entry.name != "input":
                    async with aiofiles.open(entry, "rb") as f:
                        data = await f.read()
                        new_id = uuid.uuid4()
                        await upload_file(f"worker/{new_id}_{entry.name}", data)
                        json_file = await crud.add_file(
                            self.db,
                            entry.name,
                            bucket=settings.minio_default_bucket,
                            path=f"worker/{new_id}_{entry.name}",
                            id=new_id,
                            c2_implant_id=c2_implant_id,
                            filetype=schemas.FileType.bloodhound_json,
                        )
                        log.info(f"Created new bloodhound_json file: {json_file.id}")
                        await self.process_file(str(json_file.id))


class TruffleHogParser(SimpleMatchParser):
    needle = [""]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        async with aiofiles.tempfile.TemporaryDirectory() as dir:
            d = Path(dir)
            async with aiofiles.open(d / "input", "w") as f:
                await f.write(text)

            proc = await create_subprocess_exec(
                settings.trufflehog,
                "filesystem",
                "-j",
                "--no-update",
                "--no-verification",
                d / "input",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            results: list[schemas.TruffleHogOutput] = []
            result_log = f"[exited with {proc.returncode}]\n"
            if stdout:
                result_log += "[stdout]\n"
                for line in stdout.decode().split("\n"):
                    result_log += f"{line}\n"
                    try:
                        pdata = schemas.TruffleHogOutput.model_validate_json(line)
                        results.append(pdata)
                    except json.decoder.JSONDecodeError:
                        pass
                    except ValidationError:
                        pass
            if results:
                if stderr:
                    result_log += f"[stderr]\n{stderr.decode()}"

                presult = await crud.create_parse_result(
                    self.db,
                    schemas.ParseResultCreate(
                        file_id=file_id,
                        c2_task_output_id=c2_output_id,
                        parser="trufflehog",
                        log=result_log,
                    ),
                )
                for result in results:
                    line_number: int | None = None
                    if result.source_meta_data:
                        line_number = result.source_meta_data.data.filesytem.line

                    await crud.create_highlight(
                        self.db,
                        schemas.HighlightCreate(
                            file_id=file_id,
                            c2_task_output_id=c2_output_id,
                            hit=result.raw,
                            line=line_number,
                            rule_id=result.detector_type,
                            rule_type=result.detector_name,
                            parse_result_id=presult.id,
                        ),
                    )
                    if file_id:
                        await crud.create_label_item(
                            self.db,
                            schemas.LabeledItemCreate(
                                label_id="34f0b6d4-8fcf-4296-b8e3-013a86363452",
                                file_id=file_id,
                            ),
                        )
                        await crud.create_label_item(
                            self.db,
                            schemas.LabeledItemCreate(
                                label_id="cc079c9e-3a92-41ca-9296-46ff64612d17",
                                file_id=file_id,
                            ),
                        )
                    if c2_output_id:
                        await crud.create_label_item(
                            self.db,
                            schemas.LabeledItemCreate(
                                label_id="34f0b6d4-8fcf-4296-b8e3-013a86363452",
                                c2_task_output_id=c2_output_id,
                            ),
                        )
                        await crud.create_label_item(
                            self.db,
                            schemas.LabeledItemCreate(
                                label_id="cc079c9e-3a92-41ca-9296-46ff64612d17",
                                file_id=file_id,
                            ),
                        )
                log.info(f"Found {len(results)} potential lines with credentials with TruffleHog")


class NoseyParkerParser(SimpleMatchParser):
    needle = [""]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        async with aiofiles.tempfile.TemporaryDirectory() as dir:
            d = Path(dir)
            async with aiofiles.open(d / "input", "w") as f:
                await f.write(text)

            proc = await create_subprocess_exec(
                settings.noseyparker,
                "scan",
                d / "input",
                cwd=d,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await proc.communicate()
            result_log = "[noseyparker scan stdout]\n"
            if stdout:
                result_log += stdout.decode()
            
            result_log += "[noseyparker report stdout]\n"
            proc = await create_subprocess_exec(
                settings.noseyparker,
                "report",
                "--format",
                "json",
                cwd=d,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, _ = await proc.communicate()

            if stdout:
                result_log += f"{stdout.decode()}"
                presult = await crud.create_parse_result(
                    self.db,
                    schemas.ParseResultCreate(
                        file_id=file_id,
                        c2_task_output_id=c2_output_id,
                        parser="noseyparker",
                        log=result_log,
                    ),
                )
                adapter = TypeAdapter(list[schemas.NoseyParkerOutput])
                try:
                    data = adapter.validate_json(stdout.decode())
                except ValidationError:
                    log.warning("Validation error processing NoseyParker output")
                    data = []

                for result in data:
                    for match in result.matches:
                        await crud.create_highlight(
                            self.db,
                            schemas.HighlightCreate(
                                file_id=file_id,
                                c2_task_output_id=c2_output_id,
                                hit=match.snippet.matching,
                                rule_type=match.rule_name,
                                start=match.location.source_span.start.column,
                                end=match.location.source_span.end.column,
                                line=match.location.source_span.start.line,
                                parse_result_id=presult.id,
                            ),
                        )
                    if file_id:
                        await crud.create_label_item(
                            self.db,
                            schemas.LabeledItemCreate(
                                label_id="34f0b6d4-8fcf-4296-b8e3-013a86363452",
                                file_id=file_id,
                            ),
                        )
                        await crud.create_label_item(
                            self.db,
                            schemas.LabeledItemCreate(
                                label_id="d4ace6dc-bd6b-4958-ba4a-8c47d8760c9f",
                                file_id=file_id,
                            ),
                        )
                    if c2_output_id:
                        await crud.create_label_item(
                            self.db,
                            schemas.LabeledItemCreate(
                                label_id="34f0b6d4-8fcf-4296-b8e3-013a86363452",
                                c2_task_output_id=c2_output_id,
                            ),
                        )
                        await crud.create_label_item(
                            self.db,
                            schemas.LabeledItemCreate(
                                label_id="d4ace6dc-bd6b-4958-ba4a-8c47d8760c9f",
                                file_id=file_id,
                            ),
                        )
                if data:
                    log.info(f"Found {len(data)} potential lines with credentials with NoseyParker")


class CertifpyNTLMParser(SimpleMatchParser):
    needle = ["[*] Got hash for "]


    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        needle_offset = text.find(self.needle[0])
        data = text[needle_offset+len(self.needle[0]):]
        data = data.strip()
        username, __build_class__, nt = data.split(':', 2)
        username = username.replace("'", '')
        username, domain = username.split('@', 1)
        if username and domain and nt:
            domain_obj = await crud.get_or_create_domain(self.db, domain)
            password = await crud.get_or_create_password(
                self.db, nt_hash=nt
            )
            cred = await crud.get_or_create_credential(
                self.db, username, domain_obj.id, password.id
            )
            log.info(f"Added Credential with id: {cred.id}")


class MachineAccountQuotaParser(SimpleMatchParser):
    needle = ["[+] Machine account quota (ms-DS-MachineAccountQuota):"]
    labels = ["1c2ef389-ccd3-46f7-bcaf-3d6b978b56ae"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        domain_id = None
        if c2_implant_id:
            implant = await crud.get_c2_implant(c2_implant_id)
            if implant and implant.host_id:
                host = await crud.get_host(implant.host_id)
                if host:
                    domain_id = host.domain_id
        try:
            machine_account_quota = int(text.split(':')[-1].strip())
            await crud.get_or_create_situational_awareness(
                self.db,
                sa=schemas.SituationalAwarenessCreate(
                    name=schemas.SANames.machine_account_quota,
                    category=schemas.SACategories.domain,
                    value_int=machine_account_quota,
                    domain_id=domain_id,
                ),
            )
        except ValueError:
            pass


class DomainInfoParser(SimpleMatchParser):
    needle = ["[+] DomainName:"]
    labels = ["ef240704-0cf9-4cf4-9404-73ab08581f93"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        pass


class NetViewParser(SimpleMatchParser):
    needle = ["Importing targets"]
    labels = ['6849c996-f5ab-462a-96c3-8ae891134c56']

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        count = 0
        async with get_async_neo4j_session_context() as graphsession:
            for line in text.split("\n"):
                if "logged in LOCALLY" in line:
                    host, _, user, *_ = line.split(' ')
                    try:
                        _ = ipaddress.ip_address(host)
                        log.info(f"Skipping host {host} as its an ip address")
                    except ValueError:
                        pass

                    domain = ""
                    user = user.upper()
                    host = host.upper()
                    host = host.replace(":", "")
                    if "\\" in user:
                        domain, user = user.split("\\", 1)

                    if user.endswith("$"):
                        log.info(f"Skipping computer account: {user}")
                        continue

                    if '.' in host and host.split('.', 1)[0] == domain:
                        log.info(f"Skipping user: {user} with domain: {domain} as its a local account")
                        continue

                    domain_db = await crud.get_or_create_domain(self.db, domain)
                    if not domain_db.long_name:
                        log.info(f"Skipping user: {user} with domain: {domain} as there is no long name set.")
                        continue

                    f'{user}@{domain_db.long_name.upper()} host.upper()'

                    res = await graph_crud.add_session(graphsession, host, f'{user}@{domain_db.long_name.upper()}')
                    if res:
                        count += 1
                    else:
                        log.info(f"Unable to create session: {host}-[:HasSession]->{user}@{domain_db.long_name.upper()}")
        if count:
            log.info(f"Created {count} sessions in neo4j.")


class RubeusKirbiParser(SimpleMatchParser):
    needle = ["doI"]
    labels = ["4bf0c79a-6994-4324-9cf6-0dfef6e37551"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        for line in text.splitlines():
            line = line.strip()
            if line.startswith(self.needle[0]):
                try:
                    ticket_decoded = b64decode(line)
                    await parse_ccache(self.db, ticket_decoded)
                except Exception as e:
                    log.warning(f"Caught exception: {e} while trying to parse rubeus kirbi")


class SecretsDumpParser(RegexMatchParser):
    needle = [r"(.*)\\([^:]*):[0-9]*:[A-Fa-f0-9]{32}:([A-Fa-f0-9]{32})"]
    labels = ["7af1ae71-851a-40d3-83c3-90a31f974172"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        for n in self.needle:
            tester = re.compile(n)
            for hit in tester.findall(text):
                domain, username, nt = hit
                if username and domain and nt:
                    domain_obj = await crud.get_or_create_domain(self.db, domain)
                    password = await crud.get_or_create_password(
                        self.db, nt_hash=nt
                    )
                    cred = await crud.get_or_create_credential(
                        self.db, username, domain_obj.id, password.id
                    )
                    log.info(f"Added Credential with id: {cred.id}")


class ADCSEnumBofParser(SimpleMatchParser):
    needle = ["adcs_enum SUCCESS"]
    labels = ["dc8cf07e-758e-4200-b59a-6f3682fe0a47"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        pass


class LLMParser(SimpleMatchParser):
    needle = [""]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        if not settings.gemini_enabled:
            log.info("Gemini not enabled, skipping")
            return
        try:
            results = await genai.find_credentials(text)
            presult = await crud.create_parse_result(
                self.db,
                schemas.ParseResultCreate(
                    file_id=file_id,
                    c2_task_output_id=c2_output_id,
                    parser="gemini",
                    log=str(results),
                ),
            )
            count = 0
            for result in results.credentials:
                # Check that Gemini actually gave a password and that the password is actually located in the text
                # this should reduce the false positives by quite a lot.
                if result.password and result.password in text and result.username and result.username in text:
                    count += 1
                    await crud.create_highlight(
                        self.db,
                        schemas.HighlightCreate(
                            file_id=file_id,
                            c2_task_output_id=c2_output_id,
                            hit=result.password,
                            rule_type=settings.gemini_model,
                            parse_result_id=presult.id,
                        ),
                    )
            if count:
                if file_id:
                    await crud.create_label_item(
                        self.db,
                        schemas.LabeledItemCreate(
                            label_id="34f0b6d4-8fcf-4296-b8e3-013a86363452",
                            file_id=file_id,
                        ),
                    )
                    await crud.create_label_item(
                        self.db,
                        schemas.LabeledItemCreate(
                            label_id="1cfc451f-4a4b-4ed8-aca1-544211058bdf",
                            file_id=file_id,
                        ),
                    )
                if c2_output_id:
                    await crud.create_label_item(
                        self.db,
                        schemas.LabeledItemCreate(
                            label_id="34f0b6d4-8fcf-4296-b8e3-013a86363452",
                            c2_task_output_id=c2_output_id,
                        ),
                    )
                    await crud.create_label_item(
                        self.db,
                        schemas.LabeledItemCreate(
                            label_id="1cfc451f-4a4b-4ed8-aca1-544211058bdf",
                            file_id=file_id,
                        ),
                    )
            log.info(f"Found {count} potential credentials with Gemini")
        except TypeError:
            log.warning('TypeError while processing text')
        except Exception as e:
            log.error(f'Exception {e} while processing text')


class NetShareParser(SimpleMatchParser):
    needle = ["Share:"]
    labels = ["e23ac488-0c39-49b6-897c-ab7bff23f69a"]

    async def parse(
        self,
        text: str,
        c2_implant_id: str | UUID4 | None = None,
        c2_output_id: str | UUID4 | None = None,
        file_id: str | UUID4 | None = None,
    ) -> None:
        lines = text.splitlines()
        if len(lines) < 2:
            log.warning("Probably not share output")
            return
    
        hostname = lines[1].replace('-', '')
        shares = lines[2:]
        unc_path_host = hostname

        if "." in hostname:
            hostname, domain = hostname.split(".", 1)
            domain_id = None
            if domain:
                d = await crud.get_or_create_domain(self.db, domain)
                domain_id = d.id

        _, h = await crud.get_or_create_host(self.db, hostname, domain_id)
        host_id = h.id

        await crud.create_label_item(self.db, schemas.LabeledItemCreate(
            label_id='e6a57aae-993a-4196-a23a-13a7e5f607a3',
            host_id=host_id,
        ))

        for share in shares:
            created, share_db = await crud.get_or_create_share(
                self.db,
                schemas.ShareCreate(
                    host_id=host_id,
                    name=share,
                    unc_path=f"\\\\{unc_path_host}\\{share}",
                ),
            )
            if created:
                log.info(
                    f"Created new share with name: {share_db.unc_path} ({share_db.id})"
                )


OUTPUT_PARSERS: list[type[OutputParser]] = [
    KirbiParser,
    EnvParser,
    IPConfigParser,
    WhoamiParser,
    SnafflerParser,
    KerberosHashParser,
    ASREPRoastingHashParser,
    BofRoastParser,
    LdapSearchParser,
    TruffleHogParser,
    NoseyParkerParser,
    CertifpyNTLMParser,
    MachineAccountQuotaParser,
    DomainInfoParser,
    NetViewParser,
    RubeusKirbiParser,
    SecretsDumpParser,
    ADCSEnumBofParser,
    NetShareParser,
    LLMParser,
]
