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

from harbinger.config import get_settings
from harbinger.database import database, router, models
from harbinger.database.schemas import UserRead, UserUpdate
from harbinger.database.users import auth_backend_cookie, fastapi_users
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from harbinger.files import router as files_router
from harbinger.job_templates import router as job_template_router
from harbinger.graph import router as graph_router
from fastapi_pagination import add_pagination
from harbinger.config.admin import add_admin
from harbinger.database.redis_pool import redis
from contextlib import asynccontextmanager

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Clean up the redis connection
    await redis.aclose()

app = FastAPI()

add_admin(app)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = database.SessionLocal()
        response = await call_next(request)
    finally:
        await request.state.db.close()  # type: ignore
    return response


def get_db(request: Request):
    return request.state.db


if settings.dev_mode:
    origins = [
        "http://localhost",
        "http://localhost:8080",
        "http://localhost:9000",
        "http://localhost:9002",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(router.router)
app.include_router(files_router.router)
app.include_router(job_template_router.router, prefix="/templates", tags=["templates"])

app.include_router(
    fastapi_users.get_auth_router(auth_backend_cookie), prefix="/auth", tags=["auth"]
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

app.include_router(
    graph_router.router,
    prefix="/graph",
)

app.mount("/", StaticFiles(directory="dist", html=True))

add_pagination(app)

def main():
    import uvicorn
    uvicorn.run("config.app:app", port=8080, log_level="info")
