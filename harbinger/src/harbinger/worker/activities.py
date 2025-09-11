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

from dataclasses import dataclass, field
from datetime import timedelta, datetime
import os
import dpath
import csv
from harbinger.config.process import get_process_mapping
from harbinger.graph.database import get_async_neo4j_session_context
import pytz
from temporalio import activity
from harbinger import crud
from harbinger.database import progress_bar
from harbinger import filters
from harbinger import schemas
from harbinger import models
from harbinger.database.database import SessionLocal
from harbinger.worker.genai import prompts, tools
import concurrent.futures
import structlog
import magic
import aiofiles
import asyncio
import uuid
from zipfile import ZipFile, BadZipFile
from io import BytesIO
from pydantic import ValidationError
from magika import Magika
from harbinger.files.client import download_file
from exiftool import ExifToolHelper
from exiftool.exceptions import ExifToolExecuteError
from pathlib import Path
from harbinger.worker.files import parsers
from harbinger.worker.files.keepass_parser import KeePassParser
from harbinger.files.client import upload_file, download_file
from harbinger.config import get_settings
from sqlalchemy.exc import IntegrityError
from harbinger.worker.output import OUTPUT_PARSERS, parse_ccache
from botocore.exceptions import ParamValidationError
import json
import tempfile
from harbinger.worker.files.utils import process_harbinger_yaml
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import UUID4
from sqlalchemy.orm import DeclarativeBase
from PIL import Image, ImageSequence
import math
from tabulate import tabulate
import typing as t
import rigging as rg
from sqlalchemy.exc import IntegrityError
from harbinger.graph import crud as graph_crud
from pydantic import BaseModel
import traceback
import yaml
import logging
from harbinger.enums import LlmStatus, PlanStatus, PlanStepStatus

settings = get_settings()

log = structlog.get_logger()

litellm_logger = logging.getLogger("LiteLLM")
litellm_logger.setLevel(logging.WARNING)


@activity.defn
async def check_and_finalize_plan_activity(plan_id: str) -> bool:
    """
    Checks if all steps in a plan are completed or skipped. If so,
    marks the overall plan as COMPLETED.
    """
    async with SessionLocal() as db:
        plan_steps = await crud.get_plan_steps(
            db, filters=filters.PlanStepFilter(plan_id=plan_id), limit=10000
        )

        if not plan_steps:
            # No steps, so the plan can be considered complete.
            log.info("Plan has no steps, marking as completed.", plan_id=plan_id)
            await crud.update_plan(
                db, plan_id, schemas.PlanUpdate(status=PlanStatus.COMPLETED)
            )
            return True

        for step in plan_steps:
            if step.status not in [PlanStepStatus.COMPLETED, PlanStepStatus.SKIPPED]:
                # Found a step that is not in a terminal state, so the plan is not complete.
                return False

        # If we get here, all steps are either completed or skipped.
        log.info(
            "All plan steps are in a terminal state. Marking plan as COMPLETED.",
            plan_id=plan_id,
        )
        await crud.update_plan(
            db, plan_id, schemas.PlanUpdate(status=PlanStatus.COMPLETED)
        )
        return True


@activity.defn
async def get_playbook(playbook_id: str) -> None | schemas.ProxyChain:
    playbook = await crud.get_playbook(playbook_id)
    result = None
    if playbook:
        result = schemas.ProxyChain.model_validate(playbook)
    return result


@activity.defn
async def get_playbook_steps(playbook_id: str) -> list[schemas.ChainStep]:
    result = []
    async with SessionLocal() as session:
        steps = await crud.get_playbook_steps(session, 0, 10000, playbook_id)
        for step in steps:
            result.append(schemas.ChainStep.model_validate(step))
    return result


@activity.defn
async def get_c2_implant(c2_implant_id: str) -> None | schemas.C2Implant:
    implant = await crud.get_c2_implant(c2_implant_id)
    if implant:
        return schemas.C2Implant.model_validate(implant)
    return None


@activity.defn
async def get_c2_job(job_id: str) -> None | schemas.C2Job:
    job = await crud.get_c2_job(job_id)
    if job:
        return schemas.C2Job.model_validate(job)
    return None


@activity.defn
async def get_c2_task_output(c2_task_id: UUID4) -> str:
    async with SessionLocal() as session:
        text = []
        for entry in await crud.get_c2_task_output(
            session,
            filters=filters.C2OutputFilter(c2_task_id=c2_task_id),
        ):
            text.append(entry.response_text)
        return "".join(text)


@activity.defn
async def get_proxy_job(job_id: str) -> schemas.ProxyJob:
    async with SessionLocal() as session:
        job = await crud.get_proxy_job(job_id)
        return schemas.ProxyJob.model_validate(job)


@activity.defn
async def update_playbook_status(playbook: schemas.ProxyChain) -> None:
    async with SessionLocal() as session:
        await crud.update_chain_status(
            session, playbook.status or "", playbook.id, playbook.steps or 0
        )


@activity.defn
async def update_playbook_step_status(step: schemas.ChainStep) -> None:
    async with SessionLocal() as session:
        if step.status:
            await crud.update_step_status(
                session,
                step.status,
                step.id,
            )


@activity.defn
async def update_c2_job(replace: schemas.PlaybookStepModifierEntry) -> None:
    log.info(f"Update c2 job")
    if not replace.c2_job_id:
        log.warning("c2 job id was not set.")
        return
    async with SessionLocal() as session:
        c2_job = await crud.get_c2_job(replace.c2_job_id)
        if not c2_job:
            log.warning("C2 job was not found.")
            return
        data = schemas.C2Job.model_validate(c2_job).model_dump()
        data["arguments"] = json.loads(data["arguments"])
        log.info(f"Replace before: {data}")
        dpath.set(data, replace.output_path, value=replace.data)
        log.info(f"Replace after: {data}")
        data["arguments"] = json.dumps(data["arguments"])
        update = schemas.C2JobCreate(**data)
        await crud.update_c2_job(session, replace.c2_job_id, update)


@activity.defn
async def update_c2_job_status(c2_job: schemas.C2Job):
    async with SessionLocal() as db:
        if c2_job.status:
            await crud.update_c2_job_status(
                db, c2_job_id=c2_job.id, status=c2_job.status
            )


@activity.defn
async def update_proxy_job(replace: schemas.PlaybookStepModifierEntry) -> None:
    log.info(f"Update proxy job: {replace}")
    if not replace.proxy_job_id:
        log.warning("Proxy job id was not set.")
        return
    async with SessionLocal() as session:
        proxy_job = await crud.get_proxy_job(replace.proxy_job_id)
        if not proxy_job:
            log.warning("Proxy job was not found.")
            return
        data = schemas.ProxyJob.model_validate(proxy_job).model_dump()
        log.info(f"Replace before: {data}")
        dpath.set(data, replace.output_path, value=replace.data)
        update = schemas.ProxyJobCreate(**data)
        log.info(f"Replace afer: {data}")
        await crud.update_proxy_job(session, replace.proxy_job_id, update)


@activity.defn
async def get_file(file_id: str) -> schemas.File | None:
    if file_id:
        file = await crud.get_file(file_id)
        if file:
            return schemas.File.model_validate(file)
    return None


@activity.defn
async def create_progress_bar(bar: schemas.ProgressBar) -> None:
    await progress_bar.create_progress_bar(bar)


@activity.defn
async def update_progress_bar(bar: schemas.ProgressBar) -> None:
    await progress_bar.update_progress_bar(bar.id, bar.current, bar.percentage)


@activity.defn
async def delete_progress_bar(bar: schemas.ProgressBar) -> None:
    await progress_bar.delete_progress_bar(bar.id)


FILENAME_MAP: dict[str, schemas.FileType] = {
    "output.cast": schemas.FileType.cast,
}

MAGIC_MIMETYPE_MAP: dict[str, schemas.FileType] = {
    "application/x-dmp": schemas.FileType.nanodump,
    "application/vnd.microsoft.portable-executable": schemas.FileType.exe,
    "application/zip": schemas.FileType.zip,
    "application/json": schemas.FileType.json,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": schemas.FileType.docx,
}

MAGIKA_MIMETYPE_MAP: dict[str, schemas.FileType] = {
    "application/x-dosexec": schemas.FileType.exe,
    "application/json": schemas.FileType.json,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": schemas.FileType.docx,
    "text/plain": schemas.FileType.text,
}

BYTES_MAP: dict[bytes, schemas.FileType] = {
    b"win-ad-ob": schemas.FileType.ad_snapshot,
    b"MDMP": schemas.FileType.lsass,
    b"\x03\xd9\xa2\x9ag\xfbK\xb5\x01\x00\x03\x00\x02\x10\x001\xc1\xf2\xe6\xbf": schemas.FileType.kdbx,
    b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x04\x00": schemas.FileType.dir2json,
    b"\x05\x04\x00\x0c\x00\x01\x00\x08\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x01": schemas.FileType.ccache,
}

JSON_TYPE_MAP: list[tuple[list[str | int], schemas.FileType]] = [
    (
        ["Certificate Authorities", "Certificate Templates"],
        schemas.FileType.certipy_json,
    ),
    ([0, 1], schemas.FileType.certify_json),
]


async def cast_to_text(cast_path: str, cast_bucket: str) -> str:
    data = await download_file(key=cast_path, bucket=cast_bucket)
    text_entries = []
    for line in data.splitlines()[1:]:
        entry = json.loads(line)
        if len(entry) == 3:
            text_entries.append(entry[2])

    return "\n".join(text_entries)


@activity.defn
async def update_filetype(file: schemas.File) -> None:
    async with SessionLocal() as session:
        await crud.update_file_type(session, file.id, file.filetype)


class FileParsing:
    def __init__(self) -> None:
        self.pool = concurrent.futures.ThreadPoolExecutor()

    def __del__(self):
        self.pool.shutdown()

    @activity.defn(name="file_magic_all")
    async def file_magic_all(self, file: schemas.File) -> schemas.File | None:
        try:
            data = await download_file(key=file.path, bucket=file.bucket)
        except ParamValidationError:
            log.warning("File seems to be empty")
            return None
        first_20_bytes = data[:20]
        loop = asyncio.get_event_loop()
        async with aiofiles.tempfile.NamedTemporaryFile() as tf:
            async with aiofiles.open(tf.name, "wb") as f:
                await f.write(data)
            magic_mimetype, magika_mimetype, exiftools, filetype, md5, sha1, sha256 = (
                list(
                    await asyncio.gather(
                        loop.run_in_executor(
                            self.pool, self.file_magic_sync, str(f.name)
                        ),
                        loop.run_in_executor(
                            self.pool, self.file_magika_sync, str(f.name)
                        ),
                        loop.run_in_executor(
                            self.pool, self.file_exiftool_sync, str(f.name)
                        ),
                        self.bytes_map(first_20_bytes),
                        self.generate_hash("md5", str(f.name)),
                        self.generate_hash("sha1", str(f.name)),
                        self.generate_hash("sha256", str(f.name)),
                    )
                )
            )
            file_update = schemas.FileUpdate(
                magic_mimetype=magic_mimetype,
                magika_mimetype=magika_mimetype,
                exiftool=exiftools,
                md5sum=md5,
                sha1sum=sha1,
                sha256sum=sha256,
            )
            if file.filetype:
                file_update.filetype = file.filetype
            elif filetype:
                file_update.filetype = filetype  # type: ignore
            else:
                if file.filename in FILENAME_MAP:
                    file_update.filetype = FILENAME_MAP[file.filename]
                elif file_update.magic_mimetype in MAGIC_MIMETYPE_MAP:
                    file_update.filetype = MAGIC_MIMETYPE_MAP[
                        file_update.magic_mimetype
                    ]
                elif file_update.magika_mimetype in MAGIKA_MIMETYPE_MAP:
                    file_update.filetype = MAGIKA_MIMETYPE_MAP[
                        file_update.magika_mimetype
                    ]

            async with SessionLocal() as session:
                await crud.update_file(session, file.id, file_update)
                file_db = await crud.get_file(file.id)
                if not file_db:
                    return None
                return schemas.File.model_validate(file_db)

    def file_magic_sync(self, filename: str) -> str:
        return magic.from_file(filename, mime=True)

    def file_magika_sync(self, filename: str) -> str:
        m = Magika()
        return m.identify_path(Path(filename)).output.mime_type  # type: ignore

    def file_exiftool_sync(self, filename: str) -> str:
        results: list[str] = []
        try:
            with ExifToolHelper() as et:
                for d in et.get_metadata(filename):
                    for k, v in d.items():
                        if k not in [
                            "File:FileName",
                            "File:Directory",
                            "SourceFile",
                            "ExifTool:ExifToolVersion",
                        ] and not k.startswith("JSON:"):
                            results.append(f"{k} = {v}")
        except ExifToolExecuteError:
            log.warning(f"ExifToolExecuteError")
        return "\n".join(results)

    async def generate_hash(self, hash: str, filename: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            f"{hash}sum",
            filename,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode("utf-8").split(" ")[0]

    async def bytes_map(self, first_20_bytes: bytes) -> schemas.FileType:
        for key, value in BYTES_MAP.items():
            if first_20_bytes.startswith(key):
                return value
        return schemas.FileType.empty

    @activity.defn(name="process_text")
    async def process_text(self, file: schemas.File) -> schemas.FileType:
        data = await download_file(key=file.path, bucket=file.bucket)
        text = data.decode("utf-8", errors="ignore")
        async with SessionLocal() as session:
            for Parser in OUTPUT_PARSERS:
                try:
                    p = Parser(session)
                    if await p.match(text):
                        await p.parse(text, file_id=file.id)
                        for label in p.labels:
                            await crud.create_label_item(
                                session,
                                schemas.LabeledItemCreate(
                                    label_id=label, file_id=file.id
                                ),
                            )
                except Exception as e:
                    log.error(f"Exception: {e} while running {Parser}")
        return schemas.FileType.text

    @activity.defn(name="process_unknown")
    async def process_unknown(self, file: schemas.File) -> schemas.FileType:
        data = await download_file(key=file.path, bucket=file.bucket)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            log.warning("Data not utf-8 skipping file.")
            return schemas.FileType.empty

        async with SessionLocal() as session:
            for Parser in OUTPUT_PARSERS:
                try:
                    p = Parser(session)
                    if await p.match(text):
                        await p.parse(text, file_id=file.id)
                        for label in p.labels:
                            await crud.create_label_item(
                                session,
                                schemas.LabeledItemCreate(
                                    label_id=label, file_id=file.id
                                ),
                            )
                except Exception as e:
                    log.error(f"Exception: {e} while running {Parser}")
                    traceback.print_exc()

        return schemas.FileType.empty

    @activity.defn(name="process_zip")
    async def process_zip(self, file: schemas.File) -> schemas.FileType:
        data = await download_file(key=file.path, bucket=file.bucket)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(self.pool, self.list_zip_files, data)
        bloodhound = True
        for filename in result:
            if "harbinger.yaml" in filename:
                return schemas.FileType.harbinger_zip
            if len(filename) < 14 or not filename[0:14].isdigit():
                bloodhound = False
        if bloodhound:
            return schemas.FileType.bloodhound_zip
        return schemas.FileType.zip

    def list_zip_files(self, data: bytes) -> list[str]:
        in_mem_file = BytesIO(data)
        results = []
        try:
            with ZipFile(file=in_mem_file, mode="r") as zip:
                for entry in zip.namelist():
                    results.append(entry)
        except BadZipFile:
            log.warning("Bad zip file")
        except Exception as e:
            log.error(f"Exception {e} while parsing zip file")
        return results

    @activity.defn(name="process_harbinger_zip")
    async def process_harbinger_zip(self, file: schemas.File) -> list[schemas.File]:
        data = await download_file(key=file.path, bucket=file.bucket)
        loop = asyncio.get_running_loop()
        files = []
        async with SessionLocal() as db:
            files_in_zip = await loop.run_in_executor(
                self.pool, self.extract_filenames_from_zip, data
            )
            harbinger_yaml_files = [
                file for file in files_in_zip or [] if file.endswith("harbinger.yaml")
            ]
            for harbinger_yaml in harbinger_yaml_files:
                result = await loop.run_in_executor(
                    self.pool, self.extract_file_from_zip, data, harbinger_yaml
                )
                if result:
                    log.info(f"Processing {harbinger_yaml}")
                    try:
                        for f in await process_harbinger_yaml(db, result) or []:
                            path = os.path.join("harbinger", str(f.id), f.name)
                            try:
                                file_data = await loop.run_in_executor(
                                    self.pool, self.extract_file_from_zip, data, f.path
                                )
                                if file_data:
                                    file_db = await crud.add_file(
                                        db,
                                        id=f.id,
                                        filename=f.name,
                                        bucket=settings.minio_default_bucket,
                                        path=path,
                                        filetype=f.type,
                                    )
                                    await upload_file(path, file_data)
                                    files.append(schemas.File.model_validate(file_db))
                                    log.info(f"Created {path}")
                                else:
                                    log.info(
                                        f"Unable to extract {f.name} from the zip."
                                    )
                            except IntegrityError:
                                log.info(f"{f.name} already exists, skipping")
                                await db.rollback()
                    except ValidationError:
                        log.warning(
                            f"ValidationError on parsing {harbinger_yaml} file."
                        )
        return files

    @activity.defn(name="process_harbinger_yaml")
    async def process_harbinger_yaml(self, file: schemas.File) -> list[schemas.File]:
        data = await download_file(key=file.path, bucket=file.bucket)
        async with SessionLocal() as db:
            await process_harbinger_yaml(db, data)
        return []

    def extract_file_from_zip(self, data: bytes, filename: str) -> bytes:
        in_mem_file = BytesIO(data)
        try:
            with ZipFile(file=in_mem_file, mode="r") as zip:
                return zip.read(filename)
        except BadZipFile:
            log.warning("Bad zip file")
        except Exception as e:
            log.error(f"Exception {e} while parsing zip file")
        return b""

    def extract_filenames_from_zip(self, data: bytes) -> list[str]:
        in_mem_file = BytesIO(data)
        result = []
        try:
            with ZipFile(file=in_mem_file, mode="r") as zip:
                for entry in zip.filelist:
                    if not entry.is_dir():
                        result.append(entry.filename)
        except BadZipFile:
            log.warning("Bad zip file")
        except Exception as e:
            log.error(f"Exception {e} while parsing zip file")
        return result

    @activity.defn(name="process_json")
    async def process_json(self, file: schemas.File) -> schemas.FileType:
        data = await download_file(key=file.path, bucket=file.bucket)
        async with aiofiles.tempfile.NamedTemporaryFile() as tf:
            async with aiofiles.open(tf.name, "wb") as f:
                await f.write(data)

            proc = await asyncio.create_subprocess_exec(
                f"jq",
                "-r",
                "keys",
                str(tf.name),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if stdout:
                if res := json.loads(stdout):
                    for entry in JSON_TYPE_MAP:
                        if sorted(res) == entry[0]:
                            return entry[1]
        return schemas.FileType.json

    @activity.defn(name="process_certipy_json")
    async def process_certipy_json(self, file: schemas.File) -> None:
        async with SessionLocal() as session:
            async with get_async_neo4j_session_context() as graphsession:
                p = parsers.CertipyJsonParser()
                await p.base_parse(session, graphsession, file)

    @activity.defn(name="process_certify_json")
    async def process_certify_json(self, file: schemas.File) -> None:
        async with SessionLocal() as session:
            async with get_async_neo4j_session_context() as graphsession:
                p = parsers.CertifyJsonParser()
                await p.base_parse(session, graphsession, file)

    @activity.defn(name="process_nanodump")
    async def process_nanodump(self, file: schemas.File) -> list[schemas.File]:
        async with SessionLocal() as session:
            async with get_async_neo4j_session_context() as graphsession:
                p = parsers.NanoDumpParser()
                return await p.base_parse(session, graphsession, file)

    @activity.defn(name="process_lsass")
    async def process_lsass(self, file: schemas.File) -> list[schemas.File]:
        async with SessionLocal() as session:
            async with get_async_neo4j_session_context() as graphsession:
                p = parsers.LsassParser()
                return await p.base_parse(session, graphsession, file)

    @activity.defn(name="process_ad_snapshot")
    async def process_ad_snapshot(self, file: schemas.File) -> list[schemas.File]:
        async with SessionLocal() as session:
            async with get_async_neo4j_session_context() as graphsession:
                p = parsers.ADSnapshotParser()
                return await p.base_parse(session, graphsession, file)

    @activity.defn(name="process_pypykatz")
    async def process_pypykatz(self, file: schemas.File) -> None:
        async with SessionLocal() as session:
            async with get_async_neo4j_session_context() as graphsession:
                p = parsers.PyPyKatzParser()
                await p.base_parse(session, graphsession, file)

    @activity.defn(name="process_proces_list")
    async def process_proces_list(self, file: schemas.File) -> None:
        async with SessionLocal() as session:
            async with get_async_neo4j_session_context() as graphsession:
                p = parsers.ProcessListParser()
                await p.base_parse(session, graphsession, file)

    @activity.defn(name="process_dir2json")
    async def process_dir2json(self, file: schemas.File) -> None:
        async with SessionLocal() as session:
            async with get_async_neo4j_session_context() as graphsession:
                p = parsers.Dir2JsonParser()
                await p.base_parse(session, graphsession, file)

    @activity.defn(name="process_kdbx")
    async def process_kdbx(self, file: schemas.File) -> None:
        async with SessionLocal() as session:
            async with get_async_neo4j_session_context() as graphsession:
                p = KeePassParser()
                await p.base_parse(session, graphsession, file)

    @activity.defn(name="process_cast")
    async def process_cast(self, file: schemas.File) -> None:
        text = await cast_to_text(file.path, file.bucket)
        async with SessionLocal() as session:
            for Parser in OUTPUT_PARSERS:
                try:
                    p = Parser(session)
                    if await p.match(text):
                        await p.parse(text, file_id=file.id)
                        for label in p.labels:
                            await crud.create_label_item(
                                session,
                                schemas.LabeledItemCreate(
                                    label_id=label, file_id=file.id
                                ),
                            )
                except Exception as e:
                    log.error(f"Exception: {e} while running {Parser}")
                    traceback.print_exc()

    @activity.defn(name="process_ccache")
    async def process_ccache(self, file: schemas.File) -> None:
        async with SessionLocal() as session:
            data = await download_file(file.path)
            await parse_ccache(session, data)


@activity.defn
async def label_processes(label_process: schemas.LabelProcess) -> None:
    mapping = get_process_mapping()
    log.info(
        f"Labeling processess of host: {label_process.host_id} of number: {label_process.number}, process_mapping list: {len(mapping)}"
    )
    async with SessionLocal() as db:
        processes = list(
            await crud.get_processes(
                db,
                host_id=label_process.host_id,
                number=label_process.number,
                limit=1000,
            )
        )
        log.info(f"Found {len(processes)} to potentially label")
        labels_added = set()
        count = 0
        for process in processes:
            lower = process.name.lower()
            if "\\" in lower:
                lower = lower.split("\\")[-1]
            if lower in mapping:
                create = schemas.LabeledItemCreate(
                    label_id=mapping[lower],
                    process_id=process.id,
                )
                await crud.create_label_item(db, create)
                labels_added.add(mapping[lower])
                count += 1
        for label in labels_added:
            create = schemas.LabeledItemCreate(
                label_id=label,
                host_id=label_process.host_id,
            )
            await crud.create_label_item(db, create)
        if count:
            log.info(
                f"Added labels to {count} processes and {len(labels_added)} to host {label_process.host_id}."
            )


@activity.defn
async def mark_dead() -> None:
    async with SessionLocal() as session:
        ten_min_ago = datetime.now(pytz.utc) - timedelta(minutes=10)
        c2_implants = await crud.get_c2_implants(
            session, limit=1000, not_labels=["Dead"], last_checkin_before=ten_min_ago
        )
        for c2_implant in c2_implants:
            await crud.create_label_item(
                session,
                schemas.LabeledItemCreate(
                    label_id="d734d03b-50d4-43e3-bb0e-e6bf56ec76b1",
                    c2_implant_id=c2_implant.id,
                ),
            )

        c2_implants = await crud.get_c2_implants(
            session, limit=1000, labels=["Dead"], last_checkin_after=ten_min_ago
        )

        for c2_implant in c2_implants:
            await crud.delete_label_item(
                session,
                schemas.LabeledItemDelete(
                    label_id="d734d03b-50d4-43e3-bb0e-e6bf56ec76b1",
                    c2_implant_id=c2_implant.id,
                ),
            )


@activity.defn
async def create_timeline(timeline: schemas.CreateTimeline):
    loop = asyncio.get_running_loop()
    now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    log.info("Creating timeline")

    with tempfile.TemporaryDirectory() as output_folder:
        path = Path(output_folder)
        basedir = path / "data"
        os.mkdir(basedir)
        os.mkdir(basedir / "screenshots")
        with concurrent.futures.ProcessPoolExecutor() as executor:
            headers = [
                "Timetamp (CET)",
                "Activity",
                "Source",
            ]
            attack_path: list[str] = []
            results: list[list[str]] = []
            artefacts: list[list[str]] = []
            artefact_headers = ["File Name", "File Hash (MD5)", "File Hash (SHA1)"]

            async with SessionLocal() as db:
                skip_commands: list[str] = await crud.get_setting(
                    db, "timeline", "skipped_commands", []
                )  # type: ignore
                include_status: list[str] = await crud.get_setting(
                    db,
                    "timeline",
                    "include_status",
                    ["completed", schemas.Status.error.value],
                )  # type: ignore
                ignore_labels: set[str] = set(
                    await crud.get_setting(db, "timeline", "ignore_labels", ["Test"])
                )  # type: ignore
                speed: int = await crud.get_setting(db, "timeline", "speed", 2)  # type: ignore
                idle_time: int = await crud.get_setting(db, "timeline", "idle_time", 1)  # type: ignore
                agg_timeout: int = await crud.get_setting(
                    db, "timeline", "agg_timeout", 30
                )  # type: ignore

                timeline_tasks = list(
                    await crud.get_timeline(db, status=include_status)
                )
                count = 0
                total_tasks = len(timeline_tasks)
                async with progress_bar.ProgressBar(
                    bar_id=str(uuid.uuid4()),
                    max=total_tasks + 20,
                    description="Creating timeline",
                ) as bar:
                    for db_task in timeline_tasks:
                        count += 1
                        await bar(1)
                        task: schemas.TimeLine = schemas.TimeLine.model_validate(
                            db_task
                        )

                        if task.command_name in skip_commands:
                            continue

                        labels = await crud.recurse_labels(
                            db,
                            timeline_id=task.id,
                        )
                        if set(labels) & ignore_labels:
                            continue

                        command = task.command_name or ""
                        if command in ["proxychains", "proxychains4"]:
                            command = ""

                        timestamp = ""
                        if task.time_completed:
                            timestamp = (
                                task.time_completed
                                + timedelta(hours=timeline.hour_offset)
                            ).strftime("%Y-%m-%d %H:%M:%S")
                        elif task.time_started:
                            timestamp = (
                                task.time_started
                                + timedelta(hours=timeline.hour_offset)
                            ).strftime("%Y-%m-%d %H:%M:%S")

                        if task.arguments:
                            command = f"{command} {task.arguments}"

                        if task.argument_params:
                            command = f"{command} {task.argument_params}"

                        command = command.replace("\n", "")

                        cast_file = basedir / "screenshots" / f"output_{count}.cast"
                        cast_exists = False
                        if timeline.create_screenshots:
                            if task.object_type == "C2Task":
                                log.info(
                                    f"[{count + 1}/{total_tasks}] Looking for output of {task.id}"
                                )
                                output = list(
                                    await crud.get_c2_task_output(
                                        db,
                                        filters.C2OutputFilter(c2_task_id=task.id),
                                    )
                                )
                                text = [
                                    '{"version": 2, "width": 160, "height": 46, "timestamp": 0, "env": {"SHELL": "/bin/bash", "TERM": "screen-256color"}}'
                                ]
                                c = 0
                                for o in output:
                                    for line in o.response_text.split("\n"):
                                        c += 1
                                        entry = [c / 20, "o", f"{line}\r\n"]
                                        text.append(json.dumps(entry))

                                async with aiofiles.open(cast_file, "wb") as f:
                                    await f.write("\n".join(text).encode("utf-8"))
                                cast_exists = len(output) > 0

                            if task.object_type == "ManualTimelineTask":
                                files = await crud.get_files(
                                    db,
                                    filters.FileFilter(manual_timeline_task_id=task.id),
                                )
                                if files:
                                    for file in files:
                                        if file.filetype == "cast":
                                            data = await download_file(
                                                file.path, file.bucket
                                            )
                                            async with aiofiles.open(
                                                cast_file, "wb"
                                            ) as f:
                                                await f.write(data)
                                            cast_exists = True
                                            break
                                else:
                                    text = [
                                        '{"version": 2, "width": 160, "height": 46, "timestamp": 0, "env": {"SHELL": "/bin/bash", "TERM": "screen-256color"}}'
                                    ]
                                    c = 0
                                    if task.output:
                                        for line in task.output.split("\n"):
                                            c += 1
                                            entry = [c / 20, "o", f"{line}\r\n"]
                                            text.append(json.dumps(entry))

                                        async with aiofiles.open(cast_file, "wb") as f:
                                            await f.write(
                                                "\n".join(text).encode("utf-8")
                                            )
                                        cast_exists = len(task.output) > 0

                            if task.object_type == "ProxyJob":
                                cast_files = list(
                                    await crud.get_files(
                                        db,
                                        filters.FileFilter(
                                            job_id=task.id, search="output.cast"
                                        ),
                                    )
                                )
                                if cast_files:
                                    log.info(
                                        f"[{count + 1}/{total_tasks}] Found the cast file of: {task.id}"
                                    )
                                    cf: models.File = cast_files[0]
                                    data = await download_file(cf.path, cf.bucket)

                                    async with aiofiles.open(cast_file, "wb") as f:
                                        await f.write(data)
                                    cast_exists = True

                        screenshot = False
                        screenshot_path = ""

                        if cast_exists and timeline.create_screenshots:
                            log.info(
                                f"[{count + 1}/{total_tasks}] Creating gif file for {task.id}"
                            )
                            gif_file = basedir / "screenshots" / f"output_{count}.gif"
                            proc = await asyncio.create_subprocess_exec(
                                "agg",
                                str(cast_file),
                                str(gif_file),
                                "--theme",
                                timeline.theme,
                                "--idle-time-limit",
                                str(idle_time),
                                "--speed",
                                str(speed),
                                cwd=basedir,
                            )

                            try:
                                await asyncio.wait_for(proc.wait(), int(agg_timeout))
                                screenshot_count = await loop.run_in_executor(
                                    executor,
                                    extract_screenshots,
                                    str(gif_file),
                                    str(basedir / "screenshots"),
                                    count,
                                    5,
                                )
                            except asyncio.TimeoutError:
                                proc.kill()
                                log.info("Timeout while creating screenshots.")
                                screenshot_count = 0

                            log.info(
                                f"[{count + 1}/{total_tasks}] Extracted {screenshot_count} screenshots."
                            )
                            if screenshot_count > 0:
                                screenshot = True
                                screenshot_path = (
                                    f"screenshot_{count}_{screenshot_count}.png"
                                )

                        if task.ai_summary:
                            attack_path.append(task.ai_summary)

                        if screenshot:
                            attack_path.append(f"![](screenshots/{screenshot_path})")

                        results.append(
                            [
                                timestamp,
                                command[0:400],
                                task.hostname or "",
                            ]
                        )

                    summary = ""
                    if settings.gemini_enabled:
                        log.info("Summarizing attack path")
                        try:
                            summary = await prompts.summarize_attack_path(attack_path)
                        except Exception as e:
                            log.warning(f"Unable to create attack path summary: {e}")

                    for file in await crud.get_files(
                        db, filters.FileFilter(filetype=schemas.FileType.implant_binary)
                    ):
                        artefacts.append([file.filename, file.md5sum, file.sha1sum])

                    output_table = tabulate(results, headers, tablefmt="github")
                    artefact_output = tabulate(
                        artefacts, artefact_headers, tablefmt="github"
                    )
                    with open(basedir / "timeline.md", "w") as f:
                        f.write("# Attack Path\n\n\n")
                        f.write(summary)
                        f.write("\n# Attack Path Detailed\n\n\n")
                        f.write("\n\n".join(attack_path))
                        f.write("\n\n\n# Timeline\n\n\n")
                        f.write(output_table)
                        f.write("\n\n\n# Artifacts\n\n\n")
                        f.write(artefact_output)

                    with open(basedir / "timeline.csv", "w", newline="") as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(headers)
                        for result in results:
                            writer.writerow(result)

                    await bar(5)

                    try:
                        proc = await asyncio.create_subprocess_exec(
                            "pandoc",
                            "-o",
                            "output.docx",
                            "-f",
                            "gfm",
                            "-t",
                            "docx",
                            "timeline.md",
                            cwd=basedir,
                        )
                        await proc.wait()
                        log.info(f"[pandoc exited with code: {proc.returncode}]")
                    except Exception as e:
                        log.warning(f"pandoc threw exception: {e}")

                    await bar(5)
                    proc = await asyncio.create_subprocess_exec(
                        "zip", "-r", "data.zip", "data", cwd=path
                    )

                    await proc.wait()

                    log.info(f"[zip exited with code: {proc.returncode}]")
                    await bar(5)

                    timeline_path = f"harbinger/{now}_timeline.zip"

                    with open(path / "data.zip", "rb") as f:
                        await upload_file(timeline_path, f.read())

                    await crud.add_file(
                        db,
                        filename="Timeline.zip",
                        bucket=settings.minio_default_bucket,
                        path=timeline_path,
                        filetype="zip",
                    )
                    await bar(5)
                    log.info(f"Completed uploading {timeline_path}.")


def extract_screenshots(
    input_file: str, path: str, sequence_number: int = 0, max_number: int = 5
) -> int:
    """Extract screenshots from the input gif file."""
    im = Image.open(input_file)

    if im.is_animated:  # type: ignore
        steps = math.ceil(im.n_frames / max_number)  # type: ignore

        if im.n_frames < max_number:  # type: ignore
            steps = 1

        count = 0
        seq = ImageSequence.Iterator(im)
        for i in range(0, im.n_frames, steps):  # type: ignore
            count += 1
            frame = seq[i]
            frame.save(os.path.join(path, f"screenshot_{sequence_number}_{count}.png"))
        count += 1
        frame = seq[im.n_frames - 1]  # type: ignore
        frame.save(os.path.join(path, f"screenshot_{sequence_number}_{count}.png"))
        return count
    else:
        im.save(os.path.join(path, f"screenshot_{sequence_number}_1.png"))
        return 1


@activity.defn
async def parse_output(req: schemas.TextParse) -> None:
    async with SessionLocal() as session:
        for Parser in OUTPUT_PARSERS:
            p = Parser(session)
            if await p.match(req.text):
                try:
                    await p.parse(
                        req.text,
                        c2_implant_id=req.c2_implant_id,
                        c2_output_id=req.c2_output_id,
                    )
                    for label in p.labels:
                        await crud.create_label_item(
                            session,
                            schemas.LabeledItemCreate(
                                label_id=label, c2_task_output_id=req.c2_output_id
                            ),
                        )
                except Exception as e:
                    log.error(f"Exception: {e} while running {Parser}")
                    traceback.print_exc()


@activity.defn
async def update_socks_server(socks_server: schemas.SocksServerCreate) -> None:
    async with SessionLocal() as db:
        await crud.create_socks_server(
            db,
            socks_server,
        )
        await db.commit()


@activity.defn
async def get_server_settings(c2_server_id: str) -> schemas.C2ServerAll | None:
    async with SessionLocal() as db:
        result_db = await crud.get_c2_server(db, c2_server_id)
        if not result_db:
            return None
        return schemas.C2ServerAll.model_validate(result_db)


@activity.defn
async def save_implant(c2_implant: schemas.C2ImplantCreate) -> schemas.C2Implant:
    async with SessionLocal() as db:
        domain_id = None
        if c2_implant.domain:
            domain_obj = await crud.get_or_create_domain(db, c2_implant.domain)
            domain_id = str(domain_obj.id)
        if c2_implant.hostname:
            host_created, host = await crud.get_or_create_host(
                db, c2_implant.hostname, domain_id
            )
            if host_created:
                log.info(f"Created new host: {host.id}")
            c2_implant.host_id = host.id
        created, c2_implant = await crud.create_or_update_c2_implant(db, c2_implant)
        if created:
            log.info("Created new implant.")
        return schemas.C2Implant.model_validate(c2_implant)


@activity.defn
async def save_task(c2_task: schemas.C2TaskCreate) -> schemas.C2Task:
    async with SessionLocal() as db:
        c2_implant = await crud.get_c2_implant_by_internal_id(
            db, c2_task.internal_implant_id, str(c2_task.c2_server_id)
        )
        if c2_implant:
            c2_task.c2_implant_id = c2_implant.id
        else:
            log.warning("Unable to find the implant corresponding to the task")
        created, c2_task_db = await crud.create_or_update_c2_task(db, c2_task)
        if created:
            log.info("Created new task.")

        if c2_task.command_name == "download":
            try:
                data = json.loads(c2_task.original_params or "{}")
                filename = data.get("file", "")
                log.info(f"Downloaded filename: {filename}")
                files = list(
                    await crud.get_share_files(
                        db, filters.ShareFileFilter(name=filename), limit=10
                    )
                )
                if len(files) == 1:
                    for file in files:
                        await crud.set_share_file_downloaded(db, file.id)
                files = list(
                    await crud.get_share_files(
                        db, filters.ShareFileFilter(unc_path=filename), limit=10
                    )
                )
                for file in files:
                    await crud.set_share_file_downloaded(db, file.id)
            except:
                log.warning("Unable to find the file name that was downloaded.")

        return schemas.C2Task.model_validate(c2_task_db)


@activity.defn
async def save_task_output(
    c2_task_output: schemas.C2OutputCreate,
) -> schemas.C2OutputCreated:
    async with SessionLocal() as db:
        c2_implant_id = None
        c2_task = await crud.get_c2_task_by_internal_id(
            db,
            c2_task_output.internal_task_id,
            c2_task_output.c2_server_id,
        )
        if c2_task:
            c2_task_output.c2_task_id = c2_task.id
            c2_task_output.c2_implant_id = c2_task.c2_implant_id
            c2_implant_id = c2_task.c2_implant_id
        else:
            log.warning("Unable to find the task corresponding to the output")

        if c2_task_output.bucket and c2_task_output.path:
            data = await download_file(c2_task_output.path, c2_task_output.bucket)
            c2_task_output.response_text = data.decode("utf-8", errors="replace")

        created, output_db = await crud.create_c2_task_output(db, c2_task_output)
        result = schemas.C2OutputCreated(
            created=created,
            c2_output_id=output_db.id,
            highest_process_number=0,
            c2_implant_id=c2_implant_id,
            output=c2_task_output.response_text or "",
        )
        if created and c2_task_output.processes and c2_task:
            implant = await crud.get_c2_implant(c2_task.c2_implant_id)
            if implant and implant.host_id:
                result.host_id = implant.host_id
                highest_number = await crud.get_highest_process_number(
                    db,
                    implant.host_id,
                )
                for process in c2_task_output.processes:
                    process.number = highest_number + 1
                    process.host_id = implant.host_id
                    process.c2_implant_id = implant.id
                    await crud.create_process(db, process)
                result.highest_process_number = highest_number + 1

        if c2_task_output.file_list:
            c2_task_output.file_list.parse()
            await crud.save_parsed_share_file(
                db, c2_task_output.file_list.to_base_parsed_share_file()
            )
            log.info("Processed file output.")
        if created:
            log.info("Created new task output.")
        return result


@activity.defn
async def save_proxy(proxy: schemas.ProxyCreate) -> None:
    async with SessionLocal() as db:
        created, _ = await crud.update_or_create_proxy(db, proxy)
        if created:
            log.info("Created new proxy.")


@activity.defn
async def update_c2_job_c2_task_id(c2_job_mapping: schemas.C2JobTaskMapping) -> None:
    async with SessionLocal() as db:
        await crud.update_c2_job_c2_task_id(
            db, c2_job_mapping.c2_job_id, c2_job_mapping.c2_task_id
        )


@activity.defn
async def update_c2_task_status(c2_task_status: schemas.C2TaskStatus) -> None:
    async with SessionLocal() as session:
        job = await crud.get_c2_job_status_by_task(session, c2_task_status.c2_task_id)
        if job:
            await crud.update_c2_job_status(
                session,
                job.id,
                c2_task_status.status,
                c2_task_status.message or "",
            )
            step = await crud.get_chain_step_by_c2_job_id(
                session,
                job.id,
            )
            if step:
                await crud.update_step_status(
                    session, status=c2_task_status.status, step_id=step.id
                )


@activity.defn
async def update_c2_server_status(
    c2_server_status: schemas.C2ServerStatusUpdate,
) -> None:
    async with SessionLocal() as session:
        await crud.update_c2_server_status(
            session, c2_server_status.c2_server_id, c2_server_status.status
        )


@activity.defn
async def save_file(file: schemas.FileCreate) -> schemas.File:
    async with SessionLocal() as session:
        c2_task_id = None
        if file.internal_task_id:
            c2_task = await crud.get_c2_task_by_internal_id(
                session, file.internal_task_id, str(file.c2_server_id)
            )
            if c2_task:
                c2_task_id = c2_task.id
            else:
                log.warning("Unable to find the task corresponding to the file")
        c2_implant_id = None
        if file.internal_implant_id:
            c2_implant = await crud.get_c2_implant_by_internal_id(
                session, file.internal_implant_id, str(file.c2_server_id)
            )
            if c2_implant:
                c2_implant_id = c2_implant.id
            else:
                log.warning("Unable to find the implant corresponding to the file")
        file_db = await crud.add_file(
            session,
            filename=file.filename,
            bucket=file.bucket,
            path=file.path,
            c2_task_id=c2_task_id,
            c2_implant_id=c2_implant_id,
        )
        await crud.create_label_item(
            session,
            schemas.LabeledItemCreate(
                label_id="ceccea96-9c5a-434e-ad55-e15d7c63f6ac",
                file_id=file_db.id,
            ),
        )
        return schemas.File.model_validate(file_db)


async def check_file_hash(hash_value: str) -> bool:
    async with SessionLocal() as session:
        result = await crud.get_file_by_hash(session, hash_value)
        if result:
            return True
        return False


async def create_labels_for_summary(
    db: AsyncSession,
    summary: prompts.Summary,
    c2_task_id: str | UUID4 | None = None,
    socks_task_id: str | UUID4 | None = None,
    manual_timeline_id: str | UUID4 | None = None,
) -> None:
    if summary.error:
        await crud.create_label_item(
            db,
            schemas.LabeledItemCreate(
                label_id="451c38c6-0fe0-40b0-8980-b58882bece90",
                c2_task_id=c2_task_id,
                proxy_job_id=socks_task_id,
                manual_timeline_task_id=manual_timeline_id,
            ),
        )
    if summary.successful:
        await crud.create_label_item(
            db,
            schemas.LabeledItemCreate(
                label_id="8e0b6514-56d6-40c9-8476-28f79d46d74e",
                c2_task_id=c2_task_id,
                proxy_job_id=socks_task_id,
                manual_timeline_task_id=manual_timeline_id,
            ),
        )
    if (
        summary.attack_lifecycle
        and summary.attack_lifecycle in prompts.attack_phase_label_mapping
    ):
        await crud.create_label_item(
            db,
            schemas.LabeledItemCreate(
                label_id=prompts.attack_phase_label_mapping[summary.attack_lifecycle],
                c2_task_id=c2_task_id,
                proxy_job_id=socks_task_id,
                manual_timeline_task_id=manual_timeline_id,
            ),
        )


@activity.defn
async def summarize_c2_tasks():
    log.info("Creating summaries for c2 tasks")
    if not settings.gemini_enabled:
        log.warning("Gemini not enabled, skipping")
        return
    async with SessionLocal() as db:
        for status in ["", schemas.Status.error.value]:
            skip_commands: list[str] = await crud.get_setting(
                db, "timeline", "skipped_commands", []
            )  # type: ignore
            tasks = list(
                await crud.get_c2_tasks(
                    db, filters.C2TaskFilter(processing_status=status), limit=100000
                )
            )
            async with progress_bar.ProgressBar(
                bar_id=str(uuid.uuid4()),
                max=len(tasks),
                description="Summarizing c2 tasks",
            ) as bar:
                for task in tasks:
                    await bar(1)
                    if task.command_name in skip_commands:
                        log.info(f"Skipping {task.id}: {task.command_name}")
                        await crud.update_c2_task_summary(
                            db, task.id, "", schemas.Status.skipped.value
                        )
                        continue

                    output = await crud.get_c2_task_output(
                        db, filters.C2OutputFilter(c2_task_id=task.id)
                    )
                    output_str = "".join([o.response_text for o in output])
                    try:
                        summary = await prompts.summarize_action(
                            task.command_name or "",
                            task.display_params or "",
                            output_str or "",
                        )
                        log.info(
                            f"Processed {task.id}: {task.command_name} yielding a summary of length: {len(summary.text)}"
                        )
                        await crud.update_c2_task_summary(
                            db, task.id, summary.text, schemas.Status.completed.value
                        )
                        await create_labels_for_summary(db, summary, c2_task_id=task.id)
                    except Exception as e:
                        log.error(
                            f"Exception {e} while processing task, making as error"
                        )
                        await crud.update_c2_task_summary(
                            db, task.id, "", schemas.Status.error.value
                        )


@activity.defn
async def summarize_socks_tasks():
    log.info("Creating summaries for socks tasks")
    if not settings.gemini_enabled:
        log.warning("Gemini not enabled, skipping")
        return
    async with SessionLocal() as db:
        for status in [schemas.Status.empty.value, schemas.Status.error.value]:
            skip_commands: list[str] = await crud.get_setting(
                db, "timeline", "skipped_commands", []
            )  # type: ignore
            tasks = list(
                await crud.get_proxy_jobs(
                    db, filters.SocksJobFilter(processing_status=status), limit=100000
                )
            )
            async with progress_bar.ProgressBar(
                bar_id=str(uuid.uuid4()),
                max=len(tasks),
                description="Summarizing socks tasks",
            ) as bar:
                for task in tasks:
                    await bar(1)
                    if task.command in skip_commands:
                        log.info(f"Skipping {task.id}: {task.command}")
                        await crud.update_socks_task_summary(
                            db, task.id, "", schemas.Status.skipped.value
                        )
                        continue
                    output = ""
                    cast_files = list(
                        await crud.get_files(
                            db, filters.FileFilter(job_id=task.id, search="output.cast")
                        )
                    )
                    if cast_files:
                        file = cast_files[0]
                        output = await cast_to_text(file.path, file.bucket)
                    else:
                        output_list = await crud.get_proxy_job_output(db, task.id)
                        output = "\n".join([o.output for o in output_list])

                    try:
                        summary = await prompts.summarize_action(
                            task.command or "", task.arguments or "", output or ""
                        )
                        log.info(
                            f"Processed {task.id}: {task.command} yielding a summary of length: {len(summary.text)}"
                        )
                        await crud.update_socks_task_summary(
                            db, task.id, summary.text, schemas.Status.completed.value
                        )
                        await create_labels_for_summary(
                            db, summary, socks_task_id=task.id
                        )
                    except Exception as e:
                        log.error(
                            f"Exception {e} while processing task, making as error"
                        )
                        await crud.update_socks_task_summary(
                            db, task.id, "", schemas.Status.error.value
                        )


@activity.defn
async def summarize_manual_tasks():
    log.info("Creating summaries for manual timeline entries")
    if not settings.gemini_enabled:
        log.warning("Gemini not enabled, skipping")
        return
    async with SessionLocal() as db:
        for status in [schemas.Status.empty.value, schemas.Status.error.value]:
            skip_commands: list[str] = await crud.get_setting(
                db, "timeline", "skipped_commands", []
            )  # type: ignore
            tasks = list(await crud.get_manual_timeline_tasks(db, status))
            async with progress_bar.ProgressBar(
                bar_id=str(uuid.uuid4()),
                max=len(tasks),
                description="Summarizing manual timeline tasks",
            ) as bar:
                for task in tasks:
                    await bar(1)
                    if task.command_name in skip_commands:
                        log.info(f"Skipping {task.id}: {task.command_name}")
                        await crud.update_manual_timeline_summary(
                            db, task.id, "", schemas.Status.skipped.value
                        )
                        continue
                    try:
                        summary = await prompts.summarize_action(
                            task.command_name or "",
                            task.arguments or "",
                            task.output or "",
                        )
                        log.info(
                            f"Processed {task.id}: {task.command_name} yielding a summary of length: {len(summary.text)}"
                        )
                        await crud.update_manual_timeline_summary(
                            db, task.id, summary.text, schemas.Status.completed.value
                        )
                        await create_labels_for_summary(
                            db, summary, manual_timeline_id=task.id
                        )
                    except Exception as e:
                        log.error(
                            f"Exception {e} while processing task, making as error"
                        )
                        await crud.update_manual_timeline_summary(
                            db, task.id, "", schemas.Status.error.value
                        )


def sequence_to_string_list(
    object_list: t.Iterable[DeclarativeBase], object_type: t.Type[BaseModel]
) -> list[str]:
    result: list[str] = []
    for obj in object_list:
        result.append(object_to_string(obj, object_type))
    return result


def object_to_string(
    obj: DeclarativeBase | BaseModel, object_type: t.Type[BaseModel]
) -> str:
    result = object_type.model_validate(obj)
    return result.model_dump_json(exclude_unset=True, exclude_none=True)


def dict_to_string(obj: dict) -> str:
    obj.pop("_sa_instance_state", "")
    obj.pop("processing_status", "")
    return json.dumps(obj, default=lambda o: str(o))


async def save_result(
    db: AsyncSession,
    result: prompts.Action,
    default_arguments: dict | None = None,
    c2_implant_id: str | None = None,
) -> None:
    arguments = {}
    if not default_arguments:
        default_arguments = {}
    if result.playbook and result.playbook.arguments:
        arguments = {**default_arguments, **json.loads(result.playbook.arguments)}

    if not result.playbook:
        log.info("No result :(")
        return
    else:
        log.info(result)
        if result.playbook.playbook_id == "ffffffff-ffff-ffff-ffff-ffffffffffff":
            log.info("Stop iteration")
            return

        if result.playbook.playbook_id != "ffffffff-ffff-ffff-ffff-ffffffffffff":
            try:
                _ = await crud.create_suggestion(
                    db,
                    schemas.SuggestionCreate(
                        name=result.name,
                        reason=result.reason,
                        playbook_template_id=result.playbook.playbook_id,
                        arguments=arguments,
                        c2_implant_id=c2_implant_id,
                    ),
                )
                await db.commit()
            except IntegrityError as e:
                log.warning(f"IntegrityError while creating suggestion: {e}")
                await db.rollback()


@activity.defn
async def create_c2_implant_suggestion(req: schemas.C2ImplantSuggestionRequest):
    log.info("Creating ai suggestion for specific c2 implant.")
    if not settings.gemini_enabled:
        log.warning("Gemini not enabled, skipping")
        return

    async with SessionLocal() as db:
        async with progress_bar.ProgressBar(
            bar_id=str(uuid.uuid4()),
            max=10,
            description="Creating AI suggestion",
        ) as bar:
            data = await load_data_for_ai(db, req, req.c2_implant_id)

            await bar(1)

            async def log_message(chats: list[rg.Chat]) -> None:
                for chat in chats:
                    for message in chat.generated:
                        log.info(message)

            pipeline = (
                prompts.generator.chat([{"role": "system", "content": ""}])
                .then(validate_playbook_callback(data.playbook_map))
                .watch(log_message)
                .using(data.tools)
            )
            run = prompts.suggest_action_c2_implant.bind(pipeline)

            results = await run(
                additional_prompt=req.additional_prompt,
                implant_information=data.implant_information,
            )
            await bar(4)
            arguments = dict(c2_implant_id=req.c2_implant_id)
            for result in results.actions or []:
                await save_result(db, result, arguments, req.c2_implant_id)
            await bar(1)


@activity.defn
async def create_domain_suggestion(req: schemas.SuggestionsRequest):
    log.info("Creating ai suggestion for all domains")
    if not settings.gemini_enabled:
        log.warning("Gemini not enabled, skipping")
        return

    async with SessionLocal() as db:
        async with progress_bar.ProgressBar(
            bar_id=str(uuid.uuid4()),
            max=10,
            description="Creating AI suggestion",
        ) as bar:

            async def log_message(chats: list[rg.Chat]) -> None:
                for chat in chats:
                    for message in chat.generated:
                        log.info(message)

            data = await load_data_for_ai(db, req, skip_labels=["Dead"])

            await bar(5)

            edr_detections: str = await crud.get_setting(
                db, "suggestions", "edr_detections", ""
            )  # type: ignore
            domain_checklist: str = await crud.get_setting(
                db, "suggestions", "domain_checklist", ""
            )  # type: ignore

            pipeline = (
                prompts.generator.chat([{"role": "system", "content": ""}])
                .then(validate_playbook_callback(data.playbook_map))
                .watch(log_message)
                .using(data.tools)
            )
            run = prompts.suggest_domain_action.bind(pipeline)

            try:
                results = await run(
                    edr_detections=edr_detections,
                    domain_checklist=domain_checklist,
                    additional_prompt=req.additional_prompt,
                )
                await bar(4)
                for result in results.actions or []:
                    await save_result(db, result, None)
                await bar(1)
            except Exception as e:
                log.warning(f"Exception while creating suggestions: {e}")


@activity.defn
async def create_file_download_suggestion(req: schemas.SuggestionsRequest):
    if not settings.gemini_enabled:
        log.warning("Gemini not enabled, skipping")
        return

    async def log_message(chats: list[rg.Chat]) -> None:
        for chat in chats:
            for message in chat.generated:
                log.info(message)

    log.info("Creating ai suggestion for files")
    async with SessionLocal() as db:
        async with progress_bar.ProgressBar(
            bar_id=str(uuid.uuid4()),
            max=10,
            description="Creating ai suggestion for files",
        ) as bar:
            pipeline = (
                prompts.generator.chat([{"role": "system", "content": ""}])
                .watch(log_message)
                .using(
                    [tools.get_all_c2_implant_info, tools.get_undownloaded_share_files]
                )
            )
            await bar(1)
            run = prompts.suggest_file_download_actions.bind(pipeline)
            interesting_files: str = await crud.get_setting(
                db, "suggestions", "interesting_files", ""
            )  # type: ignore
            suggestions: dict[str, list[prompts.File]] = dict()
            result = await run(
                interesting_files=interesting_files,
            )
            if result.files and result.c2_implant_id:
                if not result.c2_implant_id in suggestions:
                    suggestions[result.c2_implant_id] = []
                suggestions[result.c2_implant_id].extend(result.files)

            for c2_implant_id, files in suggestions.items():
                file_names: list[str] = []
                for file in files:
                    unc_path = file.unc_path
                    if "\\\\\\\\" in unc_path:
                        unc_path = unc_path.replace("\\\\", "\\")
                    file_names.append(unc_path)

                _ = await crud.create_suggestion(
                    db,
                    schemas.SuggestionCreate(
                        name=f"Download {len(files)} files",
                        reason="\n".join(
                            [f"{file.unc_path}: {file.reason}" for file in files]
                        ),
                        playbook_template_id="bc182f94-4f59-498c-abc8-bdf7d1bcb448",
                        arguments=dict(
                            target_files="|".join(file_names),
                            c2_implant_id=c2_implant_id,
                        ),
                    ),
                )
                await db.commit()


@activity.defn
async def create_dir_ls_suggestion(req: schemas.SuggestionsRequest):
    if not settings.gemini_enabled:
        log.warning("Gemini not enabled, skipping")
        return

    async def log_message(chats: list[rg.Chat]) -> None:
        for chat in chats:
            for message in chat.generated:
                log.info(message)

    log.info("Creating ai suggestion for dir listing")
    async with SessionLocal() as db:
        async with progress_bar.ProgressBar(
            bar_id=str(uuid.uuid4()),
            max=10,
            description="Creating ai suggestion for dir listing",
        ) as bar:
            pipeline = (
                prompts.generator.chat([{"role": "system", "content": ""}])
                .watch(log_message)
                .using(
                    [tools.get_all_c2_implant_info, tools.get_unindexed_share_folders]
                )
            )
            run = prompts.suggest_dir_list_actions.bind(pipeline)
            suggestions: dict[str, list[prompts.File]] = dict()
            await bar(1)
            result = await run()
            log.info(result)
            if result.files and result.c2_implant_id:
                if result.c2_implant_id not in suggestions:
                    suggestions[result.c2_implant_id] = []
                suggestions[result.c2_implant_id].extend(result.files)
            for c2_implant_id, files in suggestions.items():
                directories: list[str] = []
                for file in files:
                    unc_path = file.unc_path
                    if "\\\\\\\\" in unc_path:
                        unc_path = unc_path.replace("\\\\", "\\")
                    directories.append(unc_path)
                _ = await crud.create_suggestion(
                    db,
                    schemas.SuggestionCreate(
                        name=f"List {len(files)} directories",
                        reason="\n".join(
                            [f"{file.unc_path}: {file.reason}" for file in files]
                        ),
                        playbook_template_id="b13e64a7-5623-4d69-bb6e-5718b887658c",
                        arguments=dict(
                            directories="|".join(directories),
                            c2_implant_id=c2_implant_id,
                        ),
                    ),
                )
                await db.commit()


@activity.defn
async def create_share_list_suggestion(req: schemas.SuggestionsRequest):
    if not settings.gemini_enabled:
        log.warning("Gemini not enabled, skipping")
        return

    async def log_message(chats: list[rg.Chat]) -> None:
        for chat in chats:
            for message in chat.generated:
                log.info(message)

    log.info("Creating ai suggestion for share listing")
    async with SessionLocal() as db:
        async with progress_bar.ProgressBar(
            bar_id=str(uuid.uuid4()),
            max=10,
            description="Creating AI suggestion for share listing",
        ) as bar:
            pipeline = (
                prompts.generator.chat([{"role": "system", "content": ""}])
                .watch(log_message)
                .using([tools.get_all_c2_implant_info, tools.get_hosts])
            )
            run = prompts.suggest_hosts_list_shares.bind(pipeline)
            await bar(1)
            result = await run()
            chunk_size = 50
            if not result.host_list or not result.c2_implant_id:
                log.info("No hosts or c2_implants found, skipping")
                return
            for i in range(0, len(result.host_list), chunk_size):
                hosts = result.host_list[i : i + chunk_size]
                _ = await crud.create_suggestion(
                    db,
                    schemas.SuggestionCreate(
                        name=f"List shares on {len(hosts)} computers",
                        reason="\n".join(
                            [f"{host.hostname}: {host.reason}" for host in hosts]
                        ),
                        playbook_template_id="52e566d9-99a8-4aee-a0d2-2b591955f798",
                        arguments=dict(
                            computers=",".join([host.hostname for host in hosts]),
                            c2_implant_id=result.c2_implant_id,
                        ),
                    ),
                )
                await db.commit()


@activity.defn
async def create_share_root_list_suggestion(req: schemas.SuggestionsRequest):
    if not settings.gemini_enabled:
        log.warning("Gemini not enabled, skipping")
        return

    async def log_message(chats: list[rg.Chat]) -> None:
        for chat in chats:
            for message in chat.generated:
                log.info(message)

    log.info("Creating ai suggestion for listing the root of shares")
    async with SessionLocal() as db:
        async with progress_bar.ProgressBar(
            bar_id=str(uuid.uuid4()),
            max=10,
            description="Creating AI suggestion for listing the root of shares",
        ) as bar:
            pipeline = (
                prompts.generator.chat([{"role": "system", "content": ""}])
                .watch(log_message)
                .using([tools.get_network_shares, tools.get_all_c2_implant_info])
            )
            run = prompts.suggest_shares_list.bind(pipeline)
            await bar(1)
            result = await run()
            to_list = [share for share in result.share_list or []]
            if to_list:
                _ = await crud.create_suggestion(
                    db,
                    schemas.SuggestionCreate(
                        name=f"List the root of {len(to_list)} shares",
                        reason="\n".join(
                            [f"{share.share_name}: {share.reason}" for share in to_list]
                        ),
                        playbook_template_id="b13e64a7-5623-4d69-bb6e-5718b887658c",
                        arguments=dict(
                            directories="|".join(
                                [share.share_name for share in to_list]
                            ),
                            c2_implant_id=result.c2_implant_id,
                        ),
                    ),
                )
                await db.commit()
            else:
                log.info("No shares of which to list the root.")


RISK_LABEL_MAPPING: dict[int, str] = {
    1: "01dcd930-e092-4409-b0e0-355fb8a1f9ed",
    2: "492b46ff-93a0-4936-8350-220f45c4248a",
    3: "7877818c-b66c-4f82-b3b5-e5f48f5d1d0b",
    4: "bf2eb675-5b71-493d-8b05-334ff93d632d",
    5: "d2bca65c-10e0-4f33-8313-3de3b43f2fa3",
}


@activity.defn
async def c2_job_detection_risk(req: schemas.C2JobDetectionRiskRequest) -> None:
    if not settings.gemini_enabled:
        log.warning("Gemini not enabled, skipping")
        return

    async def log_message(chats: list[rg.Chat]) -> None:
        for chat in chats:
            for message in chat.generated:
                log.info(message)

    async with SessionLocal() as db:
        async with progress_bar.ProgressBar(
            bar_id=str(uuid.uuid4()),
            max=5,
            description="Checking detections",
        ) as bar:
            pipeline = prompts.generator.chat([{"role": "system", "content": ""}])
            run = prompts.c2_job_detection_risk.bind(pipeline).watch(log_message)

            c2_job = await crud.get_c2_job(req.c2_job_id)

            if not c2_job:
                log.warning(f"Unable to find the c2_job for id: {req.c2_job_id}")
                return

            c2_job_str = object_to_string(c2_job, schemas.C2Job)

            c2_implant = await crud.get_c2_implant(c2_job.c2_implant_id)

            if not c2_implant:
                log.warning(
                    f"Unable to find the implant for id: {c2_job.c2_implant_id}"
                )
                return

            await bar(1)

            labels = await crud.recurse_labels_c2_implant(db, c2_implant.id)
            labels = [l for l in labels if l.category == "EDR" or l.category == "AV"]
            c2_implant_dict = c2_implant.__dict__
            c2_implant_dict["labels"] = labels
            implant_information = dict_to_string(c2_implant_dict)
            edr_detections: str = await crud.get_setting(
                db, "suggestions", "edr_detections", ""
            )  # type: ignore

            await bar(1)
            result = await run(
                req.additional_prompt, c2_job_str, edr_detections, implant_information
            )

            await bar(1)

            log.info(f"[{req.c2_job_id}] risk: {result.value}. Reason: {result.reason}")

            if result.value not in RISK_LABEL_MAPPING:
                log.warning(
                    f"[{req.c2_job_id}] {result.value} not in RISK_LABEL_MAPPING"
                )
                return

            label_id = RISK_LABEL_MAPPING[result.value]
            await crud.create_label_item(
                db,
                schemas.LabeledItemCreate(
                    label_id=label_id,
                    c2_job_id=req.c2_job_id,
                ),
            )
            await bar(1)
            if c2_job.playbook_id:
                await crud.create_label_item(
                    db,
                    schemas.LabeledItemCreate(
                        label_id=label_id,
                        playbook_id=c2_job.playbook_id,
                    ),
                )
                await crud.send_update_playbook(
                    str(c2_job.playbook_id), "updated_chain"
                )
            await bar(1)


@activity.defn
async def kerberoasting_suggestions(req: schemas.SuggestionsRequest):
    async def log_message(chats: list[rg.Chat]) -> None:
        for chat in chats:
            for message in chat.generated:
                log.info(message)

    async with SessionLocal() as db:
        async with progress_bar.ProgressBar(
            bar_id=str(uuid.uuid4()),
            max=3,
            description="Creating kerberoasting suggestions",
        ) as bar:
            async with get_async_neo4j_session_context() as session:
                kerberoastable_users = await graph_crud.get_kerberoastable_groups(
                    session
                )
                if not kerberoastable_users:
                    await bar(3)
                    return

                await bar(1)

                data = await load_data_for_ai(db, req)
                await bar(1)

                pipeline = (
                    prompts.generator.chat([{"role": "system", "content": ""}])
                    .then(validate_playbook_callback(data.playbook_map))
                    .watch(log_message)
                    .using(data.tools)
                )
                run = prompts.kerberoasting.bind(pipeline)

                results = await run(
                    additional_prompt=req.additional_prompt,
                    kerberoastable_users=[
                        dict_to_string(user) for user in kerberoastable_users
                    ],
                )

                for result in results.actions or []:
                    await save_result(db, result, None)
                await bar(1)


def validate_playbook_callback(
    playbook_map: dict[str, models.PlaybookTemplate],
) -> t.Callable[
    [rg.Chat], t.Coroutine[t.Any, t.Any, rg.PipelineStepContextManager | None]
]:
    async def validate_playbook(
        chat: rg.Chat,
    ) -> rg.PipelineStepContextManager | None:
        """
        A rigging pipeline step that validates playbook actions and asks the LLM
        to correct them if errors are found.

        This function parses the last message for playbook actions, validates them,
        and if any errors exist, it constructs a new prompt detailing the errors
        and triggers another generation round.

        Args:
            chat: The current chat object in the rigging pipeline.

        Returns:
            A PipelineStepContextManager to trigger another LLM call if validation fails,
            otherwise None to indicate success and continue the pipeline.
        """
        error_messages = []
        try:
            # Assuming rg.parse can handle parsing the content into the desired structure
            actions = chat.last.parse(prompts.ActionList)
            for action in actions.actions or []:
                if action.playbook and action.playbook.playbook_id in playbook_map:
                    try:
                        playbook_template = playbook_map[action.playbook.playbook_id]
                        chain = schemas.PlaybookTemplate(
                            **yaml.safe_load(playbook_template.yaml)
                        )
                        arguments = json.loads(action.playbook.arguments or "{}")
                        # This line performs the actual validation
                        chain.create_model()(**arguments)
                    except ValidationError as e:
                        error_messages.append(
                            f"Validation Error for playbook '{action.playbook.playbook_id}':\n{e.json()}"
                        )
                    except (json.JSONDecodeError, yaml.YAMLError) as e:
                        error_messages.append(
                            f"Error processing playbook '{action.playbook.playbook_id}': {e}"
                        )
                # You can add other checks for placeholder IDs or missing playbooks if needed
                elif not action.playbook or not action.playbook.playbook_id:
                    error_messages.append(
                        f"Action is missing a playbook or playbook_id: {action}"
                    )
                elif action.playbook.playbook_id not in playbook_map:
                    error_messages.append(
                        f"Playbook with ID '{action.playbook.playbook_id}' not found."
                    )

        except ValidationError as e:
            log.warning(f"Major ValidationError during parsing: {e}")
            error_messages.append(
                f"The overall structure of your response was incorrect: {e.json()}"
            )

        # --- This is the key change in logic ---
        if error_messages:
            # 1. Format the collected errors into a clear message for the model.
            error_summary = "\n- ".join(error_messages)
            correction_prompt = (
                "Your previous attempt to generate a playbook action had errors. "
                "Please review the errors below, correct them, and provide the full, valid action again.\n\n"
                "Errors found:\n"
                f"- {error_summary}"
            )

            # 2. Create a new chat object with the corrective prompt.
            follow_up_chat = chat.continue_(correction_prompt)

            # 3. Return the PipelineStepContextManager to trigger a new LLM call.
            return follow_up_chat.step()

        # 4. If there were no errors, return None to exit the loop.
        return None

    return validate_playbook


@dataclass
class AIData:
    implant_information: str = ""
    playbook_map: dict[str, models.PlaybookTemplate] = field(default_factory=dict)
    tools: list[rg.Tool] = field(default_factory=list)
    domain_map: dict[str, models.Domain] = field(default_factory=dict)


async def load_data_for_ai(
    db: AsyncSession,
    req: schemas.SuggestionBaseRequest,
    c2_implant_id: str | None = None,
    include_labels: list[str] | None = None,
    skip_labels: list[str] | None = None,
) -> AIData:
    data = AIData(
        tools=[
            tools.get_playbook_templates,
            tools.get_previous_suggestions,
            tools.get_socks_servers_info,
            tools.get_situational_awareness_info,
            tools.list_filters,
        ]
    )
    if c2_implant_id:
        c2_implant = await crud.get_c2_implant(c2_implant_id)
        if c2_implant:
            labels = await crud.recurse_labels_c2_implant(db, c2_implant_id)
            c2_implant_dict = c2_implant.__dict__
            c2_implant_dict["labels"] = labels
            data.implant_information = dict_to_string(
                c2_implant_dict,
            )
    else:
        data.tools.append(tools.get_all_c2_implant_info)

    if req.c2_tasks:
        data.tools.append(tools.get_c2_tasks_executed)
    if req.c2_task_output:
        data.tools.append(tools.get_c2_tasks_executed)

    playbook_templates = await crud.get_chain_templates(
        db, filters=filters.PlaybookTemplateFilter()
    )
    data.playbook_map = {
        str(playbook_template.id): playbook_template
        for playbook_template in playbook_templates
    }
    if req.playbooks:
        data.tools.append(tools.get_playbooks)

    if req.proxies:
        data.tools.append(tools.get_proxies_info)

    if req.credentials:
        data.tools.append(tools.get_credentials_info)

    domains = await crud.get_domains(
        db,
        filters.DomainFilter(),
        limit=100000,
    )

    data.domain_map = {
        **{domain.short_name: domain for domain in domains},
        **{domain.long_name: domain for domain in domains},
    }

    return data


@activity.defn
async def create_plan_activity(objective: str, name: str) -> str:
    """
    Activity to generate the initial plan using an LLM. This remains an activity
    as it's a discrete, user-initiated task that benefits from Temporal's durability.
    """
    activity.logger.info(f"Generating plan '{name}' for objective: {objective}")

    current_state = "Use the tools to retrieve the current state of the assignement."

    async def log_message(chats: list[rg.Chat]) -> None:
        for chat in chats:
            for message in chat.generated:
                log.info(message)

    pipeline = (
        prompts.generator.chat()
        .watch(log_message)
        .using(
            [
                tools.get_all_c2_implant_info,
                tools.get_c2_tasks_executed,
                tools.get_playbooks,
                tools.get_playbook_templates,
                tools.get_proxies_info,
                tools.get_previous_suggestions,
                tools.get_socks_servers_info,
                tools.get_credentials_info,
                tools.get_situational_awareness_info,
                tools.get_domains_info,
                tools.get_undownloaded_share_files,
                tools.get_unindexed_share_folders,
                tools.get_hosts,
                tools.get_network_shares,
                tools.list_filters,
                tools.create_suggestion_for_plan_step,
            ]
        )
    )
    run = prompts.generate_testing_plan.bind(pipeline)
    llm_response: prompts.GeneratedPlan = await run(objective, current_state)
    print(llm_response)
    async with SessionLocal() as db:
        plan_schema = schemas.PlanCreate(name=name, objective=objective)
        _, plan = await crud.create_plan(db, plan=plan_schema)

        for step_data in llm_response.steps:
            step_schema = schemas.PlanStepCreate(
                plan_id=plan.id, **step_data.model_dump()
            )
            await crud.create_plan_step(db, plan_step=step_schema)

        activity.logger.info(
            f"Successfully created plan {plan.id} with {len(llm_response.steps)} steps."
        )
        return str(plan.id)


@activity.defn
async def set_plan_status_activity(plan_id: str, status: LlmStatus) -> None:
    """Sets the llm_status for a given plan."""
    plan_uuid = uuid.UUID(plan_id)
    async with SessionLocal() as db:
        await crud.update_plan(db, plan_uuid, schemas.PlanUpdate(llm_status=status))
    log.info("Set plan status", plan_id=plan_id, status=status)
