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
        version = struct.unpack("<I", data[8:12])[0]

        try:
            if version >= 0x00040000:
                return self._process_kdbx4_database(filename, data)
            if version == 0x00030001:
                return self._process_3x_database(data, database_name)
            if file_signature in self.processing_mapping:
                return self.processing_mapping[file_signature](data, database_name)
        except KeyError:
            log.error("KeePass signature unrecognized")
        except Exception as e:
            log.error(f"ERROR processing {filename}: {str(e)}")
        return None

    def _stringify_hex(self, hex_bytes: bytes) -> str:
        return hexlify(hex_bytes).decode("utf-8")

    def _process_1x_database(
        self,
        data: bytes,
        database_name: str,
        max_inline_size: int = 1024,
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
                expected_start_bytes = self._stringify_hex(data[index : index + uSize])
            index += uSize

        dataStartOffset = index
        firstEncryptedBytes = self._stringify_hex(data[index : index + 32])

        return f"$keepass$*2*{transform_rounds}*{dataStartOffset}*{master_seed}*{transform_seed}*{iv_parameters}*{expected_start_bytes}*{firstEncryptedBytes}"

    def _parse_kdf_parameters(self, kdf_data: bytes) -> dict:
        params = {}
        index = 0
        if not kdf_data:
            return params
        index += 2  # version
        while index < len(kdf_data):
            value_type = kdf_data[index]
            index += 1
            if value_type == 0:
                break
            key_len = struct.unpack("<I", kdf_data[index : index + 4])[0]
            index += 4
            key_name = kdf_data[index : index + key_len].decode("utf-8", errors="ignore")
            index += key_len
            val_len = struct.unpack("<I", kdf_data[index : index + 4])[0]
            index += 4
            if val_len > 0:
                value = kdf_data[index : index + val_len]
                index += val_len
                if value_type == 0x04 and val_len == 4:
                    params[key_name] = struct.unpack("<I", value)[0]
                elif value_type == 0x05 and val_len == 8:
                    params[key_name] = struct.unpack("<Q", value)[0]
                elif value_type == 0x08 and val_len == 1:
                    params[key_name] = bool(value[0])
                elif value_type == 0x18:
                    params[key_name] = value.decode("utf-8", errors="ignore")
                elif value_type == 0x42:
                    params[key_name] = value
                    if key_name == "$UUID" and len(value) >= 16:
                        params["$UUID_bytes"] = value
        return params

    def _process_kdbx4_database(self, filename: str, data: bytes) -> str:
        with open(filename, "rb") as f:
            f.seek(0)
            complete_header_data = f.read(12)
            header_fields = {}
            while True:
                field_id_byte = f.read(1)
                if not field_id_byte or field_id_byte[0] == 0:
                    break
                field_id = field_id_byte[0]
                field_size = struct.unpack("<I", f.read(4))[0]
                field_data = f.read(field_size)
                header_fields[field_id] = field_data
                complete_header_data += (
                    field_id_byte + struct.pack("<I", field_size) + field_data
                )
            header_hash = f.read(8)
            complete_header_data += b"\x00" + header_hash
            f.read(32)
            header_hmac = f.read(32)

        master_seed = header_fields.get(4, b"")
        kdf_params_data = header_fields.get(11, b"")
        kdf_params = self._parse_kdf_parameters(kdf_params_data)
        kdf_uuid_bytes = kdf_params.get("$UUID", b"")
        kdf_uuid_str = (
            f"{struct.unpack('>I', struct.pack('<I', struct.unpack('<I', kdf_uuid_bytes[:4])[0]))[0]:08x}"
            if kdf_uuid_bytes and len(kdf_uuid_bytes) >= 4
            else "00000000"
        )
        iterations = kdf_params.get("I", kdf_params.get("R", 0))
        memory = kdf_params.get("M", 0)
        parallelism = kdf_params.get("P", 0)
        salt = kdf_params.get("S", b"")
        v = kdf_params.get("V", 0)
        transform_seed = salt
        database_name = os.path.basename(filename)

        return f"$keepass$*4*{iterations}*{kdf_uuid_str}*{memory}*{v}*{parallelism}*{self._stringify_hex(master_seed)}*{self._stringify_hex(transform_seed)}*{self._stringify_hex(complete_header_data)}*{self._stringify_hex(header_hmac)}"

    def _process_3x_database(self, data: bytes, database_name: str) -> str:
        index = 12
        end_reached = False
        master_seed = b""
        transform_seed = b""
        transform_rounds = 0
        iv_parameters = b""
        expected_start_bytes = b""
        algorithm = 0
        kdf_params_data = b""

        while not end_reached:
            btFieldID = struct.unpack("B", data[index : index + 1])[0]
            index += 1
            uSize = struct.unpack("<I", data[index : index + 4])[0]
            index += 4
            if btFieldID == 0:
                end_reached = True
                continue
            # ... (rest of the parsing logic for 3.x)
            index += uSize

        header_hash = data[index : index + 32]
        index += 32
        header_hmac = data[index : index + 32]
        index += 32
        first_encrypted_bytes = data[index : index + 32]

        if kdf_params_data:
            kdf_params = self._parse_kdf_parameters(kdf_params_data)
            kdf_uuid_bytes = kdf_params.get("$UUID_bytes", b"")
            kdf_uuid_str = (
                f"{struct.unpack('<I', kdf_uuid_bytes[:4])[0]:08x}"
                if kdf_uuid_bytes and len(kdf_uuid_bytes) >= 4
                else "00000000"
            )
            kdf_uuid_str = "".join(
                [kdf_uuid_str[i : i + 2] for i in range(6, -1, -2)]
            )
            iterations = kdf_params.get("I", kdf_params.get("R", transform_rounds))
            memory = kdf_params.get("M", 0)
            parallelism = kdf_params.get("P", 0)
            salt = kdf_params.get("S", transform_seed)
            complete_header_data = data[:index]
            return f"$keepass$*4*{iterations}*{kdf_uuid_str}*{memory}*{parallelism}*{self._stringify_hex(master_seed)}*{self._stringify_hex(salt)}*{self._stringify_hex(complete_header_data)}*{self._stringify_hex(header_hmac)}"
        else:
            return f"$keepass$*3*{transform_rounds}*{algorithm}*{self._stringify_hex(master_seed)}*{self._stringify_hex(transform_seed)}*{self._stringify_hex(iv_parameters)}*{self._stringify_hex(expected_start_bytes)}*{self._stringify_hex(header_hash)}*{self._stringify_hex(header_hmac)}*{self._stringify_hex(first_encrypted_bytes)}"

    @property
    def processing_mapping(self):
        return {
            b"03d9a29a67fb4bb5": self._process_2x_database,
            b"03d9a29a66fb4bb5": self._process_2x_database,
            b"03d9a29a65fb4bb5": self._process_1x_database,
        }
