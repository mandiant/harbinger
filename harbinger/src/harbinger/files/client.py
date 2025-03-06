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

from aiobotocore.session import get_session
from harbinger.config import Settings, get_settings
from typing import TypedDict


settings: Settings = get_settings()


async def create_client():
    session = get_session()
    return session.create_client(
        "s3",
        endpoint_url=settings.minio_host,
        aws_secret_access_key=settings.minio_secret_key,
        aws_access_key_id=settings.minio_access_key,
    )


class PartInfo(TypedDict):
    ETag: str
    PartNumber: int


async def create_multipart_upload(
    key: str, bucket: str = settings.minio_default_bucket
) -> str:
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.minio_host,
        aws_secret_access_key=settings.minio_secret_key,
        aws_access_key_id=settings.minio_access_key,
    ) as client:
        resp = await client.create_multipart_upload(Bucket=bucket, Key=key)  # type: ignore
        return resp["UploadId"]  # type: ignore


async def upload_part(
    upload_id: str,
    chunk: bytes,
    chunk_number: int,
    key: str,
    bucket: str = settings.minio_default_bucket,
) -> str:
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.minio_host,
        aws_secret_access_key=settings.minio_secret_key,
        aws_access_key_id=settings.minio_access_key,
    ) as client:
        resp = await client.upload_part(
            Bucket=bucket,
            Body=chunk,
            UploadId=upload_id,
            PartNumber=chunk_number,
            Key=key,
        )  # type: ignore
        return resp['ETag']


async def complete_multipart_upload(
    upload_id: str,
    key: str,
    parts: list[PartInfo],
    bucket: str = settings.minio_default_bucket,
):
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.minio_host,
        aws_secret_access_key=settings.minio_secret_key,
        aws_access_key_id=settings.minio_access_key,
    ) as client:

        await client.complete_multipart_upload(
            Bucket=bucket,
            UploadId=upload_id,
            MultipartUpload=dict(Parts=parts),
            Key=key,
        )  # type:ignore


async def cancel_multipart_upload(
    upload_id: str,
    key: str,
    bucket: str = settings.minio_default_bucket,
):
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.minio_host,
        aws_secret_access_key=settings.minio_secret_key,
        aws_access_key_id=settings.minio_access_key,
    ) as client:
        await client.abort_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id
        )  # type: ignore


async def upload_file(
    key: str, data: bytes, bucket: str = settings.minio_default_bucket
):
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.minio_host,
        aws_secret_access_key=settings.minio_secret_key,
        aws_access_key_id=settings.minio_access_key,
    ) as client:
        try:
            await client.put_object(Bucket=bucket, Key=key, Body=data)  # type: ignore
        except client.exceptions.NoSuchBucket:
            await client.create_bucket(Bucket=bucket)  # type: ignore
            await client.put_object(Bucket=bucket, Key=key, Body=data)  # type: ignore


async def download_file(
    key: str, bucket: str = settings.minio_default_bucket, bytes_range: str = ""
) -> bytes:
    session = get_session()
    async with session.create_client(
        "s3",
        endpoint_url=settings.minio_host,
        aws_secret_access_key=settings.minio_secret_key,
        aws_access_key_id=settings.minio_access_key,
    ) as client:
        try:
            response = await client.get_object(Bucket=bucket, Key=key, Range=bytes_range)  # type: ignore
            async with response["Body"] as stream:
                return await stream.read()
        except client.exceptions.NoSuchKey:
            return b''


class FileUploader:
    """Automatically creates multipart uploads.
    Use in a context like: `async with FileUploader('path', 'bucket') as f:`
    Call upload() with your bytes.
    When the context exists it will finalize the upload.
    """

    def __init__(self, path: str, bucket: str):
        self.path = path
        self.bucket = bucket
        self.buffer = b''
        self.completed = False
        self.parts: list[PartInfo] = []
        self.counter = 1
        self.upload_id: str = ''

    async def upload(self, buffer: bytes) -> None:
        self.buffer += buffer
        if len(self.buffer) > 6291456:
            await self.upload_chunk()

    async def upload_chunk(self):
            etag = await upload_part(
                self.upload_id, self.buffer, self.counter, self.path
            )
            self.parts.append(
                PartInfo(
                    ETag=etag, PartNumber=self.counter
                )
            )
            self.buffer = b''
            self.counter += 1

    async def complete(self) -> None:
        if not self.completed:
            if self.buffer:
                await self.upload_chunk()
            if len(self.parts) > 0:
                await complete_multipart_upload(
                    self.upload_id, self.path, self.parts
                )
            else:
                await self.cancel()
            self.completed = True

    async def cancel(self) -> None:
        await cancel_multipart_upload(self.upload_id, self.path, self.bucket)

    async def __aenter__(self) -> 'FileUploader':
        self.upload_id = await create_multipart_upload(self.path)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if not exc:
            await self.complete()
        else:
            await self.cancel()
