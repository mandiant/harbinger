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

from fastapi import APIRouter, Depends, HTTPException
from harbinger.database.database import get_async_session
from harbinger.database.redis_pool import redis_no_decode as redis
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

router = APIRouter()


class HealthCheckStatus(BaseModel):
    database: str
    redis: str


@router.get(
    "/healthcheck",
    response_model=HealthCheckStatus,
    tags=["healthcheck"],
)
async def healthcheck(
    db: AsyncSession = Depends(get_async_session),
):
    """
    Checks the health of the application and its services.
    """
    db_status = "ok"
    redis_status = "ok"

    try:
        # Check database connection
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        # Check redis connection
        await redis.ping()
    except Exception:
        redis_status = "error"

    if db_status == "error" or redis_status == "error":
        raise HTTPException(
            status_code=503,
            detail={"database": db_status, "redis": redis_status},
        )

    return HealthCheckStatus(database=db_status, redis=redis_status)
