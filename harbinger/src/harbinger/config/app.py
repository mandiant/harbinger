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

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_pagination import add_pagination

from harbinger.api.v1.endpoints import (
    actions,
    c2_implants,
    c2_jobs,
    c2_output,
    c2_server_arguments,
    c2_server_types,
    c2_servers,
    c2_tasks,
    certificate_authorities,
    certificate_templates,
    checklists,
    create_summaries,
    create_timeline,
    credentials,
    domains,
    events,
    files,
    files_root,
    graph,
    hashes,
    healthcheck,
    highlights,
    hosts,
    issues,
    item_label,
    job_templates,
    kerberos,
    label_categories,
    labels,
    llm_logs,
    manual_timeline_tasks,
    objectives,
    parse_results,
    passwords,
    plan_steps,
    plans,
    playbooks,
    processes,
    progress_bars,
    proxies,
    proxy_job_output,
    proxy_jobs,
    search,
    share_files,
    shares,
    situational_awareness,
    socks_servers,
    statistics,
    step_modifiers,
    steps,
    suggestions,
    timeline,
    ws,
)
from harbinger.api.v1.endpoints import (
    settings as settings_router,
)
from harbinger.config import get_settings
from harbinger.config.admin import add_admin
from harbinger.database import database
from harbinger.database.redis_pool import redis
from harbinger.database.users import auth_backend_cookie, fastapi_users
from harbinger.schemas import UserRead, UserUpdate

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
app.include_router(ws.router, prefix="/ws", tags=["ws"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(actions.router, prefix="/actions", tags=["actions"])
app.include_router(c2_implants.router, prefix="/c2_implants", tags=["c2"])
app.include_router(c2_jobs.router, prefix="/c2_jobs", tags=["c2"])
app.include_router(c2_output.router, prefix="/c2_output", tags=["c2"])
app.include_router(
    c2_server_arguments.router,
    prefix="/c2_server_arguments",
    tags=["c2_server_arguments"],
)
app.include_router(
    c2_server_types.router,
    prefix="/c2_server_types",
    tags=["c2_server_types"],
)
app.include_router(c2_servers.router, prefix="/c2_servers", tags=["c2"])
app.include_router(c2_tasks.router, prefix="/c2_tasks", tags=["c2"])
app.include_router(
    certificate_authorities.router,
    prefix="/certificate_authorities",
    tags=["certificate_authorities"],
)
app.include_router(
    certificate_templates.router,
    prefix="/certificate_templates",
    tags=["certificate_templates"],
)
app.include_router(checklists.router, prefix="/checklist", tags=["checklists"])
app.include_router(
    create_summaries.router,
    prefix="/create_summaries",
    tags=["create_summaries"],
)
app.include_router(
    create_timeline.router,
    prefix="/create_timeline",
    tags=["create_timeline"],
)
app.include_router(credentials.router, prefix="/credentials", tags=["credentials"])
app.include_router(domains.router, prefix="/domains", tags=["domains"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(files_root.router, prefix="", tags=["files_root"])
app.include_router(graph.router, prefix="/graph", tags=["graph"])
app.include_router(hashes.router, prefix="/hashes", tags=["hashes"])
app.include_router(healthcheck.router, prefix="", tags=["healthcheck"])
app.include_router(highlights.router, prefix="/highlights", tags=["highlights"])
app.include_router(hosts.router, prefix="/hosts", tags=["hosts"])
app.include_router(issues.router, prefix="/issues", tags=["issues"])
app.include_router(item_label.router, prefix="/item_label", tags=["item_label"])
app.include_router(job_templates.router, prefix="/templates", tags=["templates"])
app.include_router(kerberos.router, prefix="/kerberos", tags=["kerberos"])
app.include_router(
    label_categories.router,
    prefix="/label_categories",
    tags=["label_categories"],
)
app.include_router(labels.router, prefix="/labels", tags=["labels"])
app.include_router(llm_logs.router, prefix="/llm_logs", tags=["llm_logs"])
app.include_router(
    manual_timeline_tasks.router,
    prefix="/manual_timeline_tasks",
    tags=["manual_timeline_tasks"],
)
app.include_router(objectives.router, prefix="/objectives", tags=["objectives"])
app.include_router(
    parse_results.router,
    prefix="/parse_results",
    tags=["parse_results"],
)
app.include_router(passwords.router, prefix="/passwords", tags=["passwords"])
app.include_router(plan_steps.router, prefix="/plan_steps", tags=["plan_steps"])
app.include_router(plans.router, prefix="/plans", tags=["plans"])
app.include_router(playbooks.router, prefix="/playbooks", tags=["playbooks"])
app.include_router(processes.router, prefix="/processes", tags=["processes"])
app.include_router(
    progress_bars.router,
    prefix="/progress_bars",
    tags=["progress_bars"],
)
app.include_router(proxies.router, prefix="/proxies", tags=["proxies"])
app.include_router(
    proxy_job_output.router,
    prefix="/proxy_job_output",
    tags=["proxy_job_output"],
)
app.include_router(proxy_jobs.router, prefix="/proxy_jobs", tags=["proxy_jobs"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(settings_router.router, prefix="/settings", tags=["settings"])
app.include_router(share_files.router, prefix="/share_files", tags=["share_files"])
app.include_router(shares.router, prefix="/shares", tags=["shares"])
app.include_router(
    situational_awareness.router,
    prefix="/situational_awareness",
    tags=["situational_awareness"],
)
app.include_router(socks_servers.router, prefix="/socks_servers", tags=["socks"])
app.include_router(
    step_modifiers.router,
    prefix="/playbook_step_modifier",
    tags=["step_modifiers"],
)
app.include_router(steps.router, prefix="/playbook_step", tags=["steps"])
app.include_router(suggestions.router, prefix="/suggestions", tags=["suggestions"])
app.include_router(timeline.router, prefix="/timeline", tags=["timeline"])
app.include_router(statistics.router, prefix="/statistics", tags=["statistics"])
app.include_router(
    fastapi_users.get_auth_router(auth_backend_cookie),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
add_pagination(app)
app.mount("/", StaticFiles(directory="dist", html=True))


def main():
    import uvicorn

    uvicorn.run("config.app:app", port=8080, log_level="info")
