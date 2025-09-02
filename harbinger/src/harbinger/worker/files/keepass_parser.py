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
import struct
from binascii import hexlify
from typing import Optional

import aiofiles
import structlog
from harbinger.database import crud, schemas
from harbinger.worker.files.parsers import BaseFileParser
from neo4j import AsyncSession as AsyncNeo4jSession
from sqlalchemy.ext.asyncio import AsyncSession

log = structlog.get_logger()


class KeePassParser(BaseFileParser):
    """Parser for KeePass kdbx files."""

    async def parse(
        self,
        db: AsyncSession,
        graph_db: AsyncNeo4jSession,
        tmpdirname: str,
        tmpfilename: str,
        file: schemas.File,
    ) -> list[schemas.File]:
        """Parses a KeePass kdbx file and extracts the hash."""
        log.info(f"Parsing KeePass file: {tmpfilename}")
        try:
            hash_string = await self._process_database(tmpfilename)
            if hash_string:
                await crud.create_hash(
                    db,
                    schemas.HashCreate(
                        hash=hash_string,
                        type="keepass",
                        hashcat_id=13400,
                    ),
                )
                log.info(f"Successfully extracted hash from {file.filename}")
        except Exception as e:
            log.error(f"Failed to parse KeePass file {file.filename}: {e}")
        return []

    async def _process_database(self, filename: str) -> Optional[str]:
        """Processes the KeePass database file to extract the hash."""
        async with aiofiles.open(filename, "rb") as f:
            data = await f.read()

        base = os.path.basename(filename)
        database_name = os.path.splitext(base)[0]

        file_signature = hexlify(data[0:8])

        try:
            return self.processing_mapping[file_signature](data, database_name)
        except KeyError:
            log.error("KeePass signature unrecognized")
        return None

    def _stringify_hex(self, hex_bytes: bytes) -> str:
        return hexlify(hex_bytes).decode("utf-8")

    def _process_1x_database(
        self, data: bytes, database_name: str, max_inline_size: int = 1024
    ) -> str:
        index = 8
        algorithm = -1

        enc_flag = struct.unpack("<L", data[index : index + 4])[0]
        index += 4
        if enc_flag & 2 == 2:
            algorithm = 0  # AES
        elif enc_flag & 8:
            algorithm = 1  # Twofish
        else:
            raise ValueError("Unsupported file encryption!")

        key_file_size = struct.unpack("<L", data[index : index + 4])[0]
        index += 4
        index += key_file_size

        index += 4  # version

        final_random_seed = self._stringify_hex(data[index : index + 16])
        index += 16

        iv_params = self._stringify_hex(data[index : index + 16])
        index += 16

        index += 4  # num_groups
        index += 4  # num_entries

        contents_hash = self._stringify_hex(data[index : index + 32])
        index += 32

        transform_random_seed = self._stringify_hex(data[index : index + 32])
        index += 32

        key_transform_rounds = struct.unpack("<L", data[index : index + 4])[0]

        filesize = len(data)
        datasize = filesize - 124

        if (filesize + datasize) < max_inline_size:
            data_buffer = hexlify(data[124:])
            end = "*1*%ld*%s" % (datasize, self._stringify_hex(data_buffer))
        else:
            end = "0*%s" % database_name

        return f"$keepass$*1*{key_transform_rounds}*{algorithm}*{final_random_seed}*{transform_random_seed}*{iv_params}*{contents_hash}*{end}"

    def _process_2x_database(self, data: bytes, database_name: str) -> str:
        index = 12
        end_reached = False
        master_seed = b""
        transform_seed = b""
        transform_rounds = 0
        iv_parameters = b""
        expected_start_bytes = b""

        while not end_reached:
            btFieldID = struct.unpack("B", data[index : index + 1])[0]
            index += 1
            uSize = struct.unpack("H", data[index : index + 2])[0]
            index += 2

            if btFieldID == 0:
                end_reached = True

            if btFieldID == 4:
                master_seed = self._stringify_hex(data[index : index + uSize])

            if btFieldID == 5:
                transform_seed = self._stringify_hex(data[index : index + uSize])

            if btFieldID == 6:
                transform_rounds = struct.unpack("Q", data[index : index + 8])[0]

            if btFieldID == 7:
                iv_parameters = self._stringify_hex(data[index : index + uSize])

            if btFieldID == 9:
                expected_start_bytes = self._stringify_hex(
                    data[index : index + uSize]
                )

            index += uSize

        dataStartOffset = index
        firstEncryptedBytes = self._stringify_hex(data[index : index + 32])

        return f"$keepass$*2*{transform_rounds}*{dataStartOffset}*{master_seed}*{transform_seed}*{iv_parameters}*{expected_start_bytes}*{firstEncryptedBytes}"

    @property
    def processing_mapping(self):
        return {
            b"03d9a29a67fb4bb5": self._process_2x_database,  # "2.X"
            b"03d9a29a66fb4bb5": self._process_2x_database,  # "2.X pre release"
            b"03d9a29a65fb4bb5": self._process_1x_database,  # "1.X"
        }