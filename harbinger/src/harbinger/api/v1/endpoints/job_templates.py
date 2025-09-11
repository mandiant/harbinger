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

import json
import uuid
from typing import Optional, Type, Union

import jsonref
import yaml
from fastapi import APIRouter, Depends, Request, Response, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, add_pagination
from pydantic import UUID4, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from harbinger import crud, models, schemas
from harbinger.config import get_settings
from harbinger.config.dependencies import current_active_user, get_db
from harbinger.database import filters
from harbinger.config.dependencies import current_active_user
from harbinger.job_templates.proxy import PROXY_JOB_BASE_MAP
from harbinger.job_templates.proxy.base import JobTemplateModel
from harbinger.job_templates.schemas import (
    C2_JOB_BASE_MAP,
    BaseTemplateModel,
    C2ImplantTemplateModel,
    TemplateList,
)
from harbinger.worker.genai import prompts

settings = get_settings()

router = APIRouter()





@router.get(
    "/playbooks/",
    response_model=Page[schemas.PlaybookTemplateView],
    tags=["proxy_jobs", "crud"],
)
async def playbook_templates(
    filters: filters.PlaybookTemplateFilter = FilterDepends(
        filters.PlaybookTemplateFilter
    ),
    user: models.User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_chain_templates_paged(db, filters)


@router.get(
    "/playbooks/filters",
    response_model=list[schemas.Filter],
    tags=["proxy_jobs", "crud"],
)
async def playbook_template_filters(
    filters: filters.PlaybookTemplateFilter = FilterDepends(
        filters.PlaybookTemplateFilter
    ),
    user: models.User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_playbook_template_filters(db, filters)


@router.get(
    "/{c2_type}/",
    response_model=TemplateList,
    tags=["proxy_jobs", "crud"],
)
async def job_templates(
    c2_type: schemas.C2Type,
    user: models.User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if c2_type == schemas.C2Type.c2:
        return dict(templates=[key for key in C2_JOB_BASE_MAP.keys()])
    if c2_type == schemas.C2Type.proxy:
        return dict(templates=[key for key in PROXY_JOB_BASE_MAP.keys()])


@router.get(
    "/playbooks/{uuid}/schema",
    tags=["proxy_jobs", "crud"],
)
async def chain_templates_schema(
    uuid: UUID4,
    suggestion_id: UUID4 | None = None,
    user: models.User = Depends(current_active_user),
    db: AsyncSession = Depends(get_db),
):
    default_arguments = {}
    if suggestion_id:
        suggestion = await crud.get_suggestion(suggestion_id)
        if suggestion:
            default_arguments = suggestion.arguments
    schema = await crud.get_playbook_template(uuid)
    if schema:
        schema_templ = schemas.PlaybookTemplate(**yaml.safe_load(schema.yaml))
        return jsonref.loads(
            json.dumps(schema_templ.create_model(default_arguments).model_json_schema())
        )
    return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.get(
    "/playbooks/{id}",
    response_model=Optional[schemas.PlaybookTemplateView],
    tags=["crud", "playbook_templates"],
)
async def get_playbook_template(
    id: UUID4,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    return await crud.get_playbook_template(id)


@router.get("/{c2_type}/{name}/schema", tags=["proxy_jobs", "crud"])
def proxy_job_templates_schema(
    c2_type: schemas.C2Type,
    name: str,
    user: models.User = Depends(current_active_user),
):
    if c2_type == schemas.C2Type.c2:
        return jsonref.loads(json.dumps(C2_JOB_BASE_MAP[name].model_json_schema()))
    if c2_type == schemas.C2Type.proxy:
        return jsonref.loads(json.dumps(PROXY_JOB_BASE_MAP[name].model_json_schema()))


@router.post(
    "/playbooks/{uuid}/preview",
    response_model=schemas.PlaybookPreview,
    tags=["c2", "crud"],
)
async def create_chain_preview_from_template(
    uuid: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    body = await request.json()
    schema = await crud.get_playbook_template(uuid)
    if schema:
        try:
            chain = schemas.PlaybookTemplate(**yaml.safe_load(schema.yaml))
            model = chain.create_model()(**body).model_dump()
        except ValidationError as e:
            return Response(e.json(), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return await crud.preview_chain_from_template(db, chain, model)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post(
    "/{c2_type}/{name}/preview",
    response_model=Union[
        schemas.ProxyJobPreview, schemas.C2JobCreate, schemas.ErrorResponse
    ],
    tags=["mythic_jobs", "crud"],
)
async def preview(
    c2_type: schemas.C2Type,
    name: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    body = await request.json()
    fake_data = dict(
        c2_implant=str(uuid.uuid4()),
        playbook_id=str(uuid.uuid4()),
    )

    job_template: type[JobTemplateModel] | type[C2ImplantTemplateModel] | None = None

    try:
        if c2_type == schemas.C2Type.c2:
            job_template = C2_JOB_BASE_MAP[name]
        if c2_type == schemas.C2Type.proxy:
            job_template = PROXY_JOB_BASE_MAP[name]
    except KeyError:
        pass

    if not job_template:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return dict(error="Not found")

    try:
        template = job_template(**body | fake_data)
    except ValidationError as e:
        return Response(e.json(), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    args = await template.generate_arguments(db)
    command = await template.generate_command()
    if c2_type == schemas.C2Type.proxy:
        socks_server = await crud.get_socks_server(template.socks_server_id)  # type: ignore
        return schemas.ProxyJobPreview(
            command=command,
            arguments=args,
            playbook_id=template.playbook_id,
            socks_server_id=template.socks_server_id,  # type: ignore
            socks_server=socks_server,
        )
    else:
        return schemas.C2JobCreate(
            command=command,
            arguments=args,
            playbook_id=template.playbook_id,
            c2_implant_id=uuid.uuid4(),
        )


async def create_c2_job(
    db: AsyncSession, template: Type[BaseTemplateModel], body: dict
) -> models.C2Job:
    template_obj = template(**body)
    args = await template_obj.generate_arguments(db)
    files = await template_obj.files(db)
    job = schemas.C2JobCreate(
        command=template_obj.Settings.command,
        arguments=args,
        input_files=files,
        playbook_id=template_obj.playbook_id,
        c2_implant_id=getattr(template_obj, "c2_implant_id"),
    )
    return await crud.create_c2_job(db, job=job)


async def create_proxy_job(
    db: AsyncSession, template: Type[JobTemplateModel], body: dict
) -> models.ProxyJob:
    template_obj = template(**body)
    args = await template_obj.generate_arguments(db)
    files = await template_obj.files(db)
    job = schemas.ProxyJobCreate(
        credential_id=getattr(template_obj, "credential_id", None),
        proxy_id=template_obj.proxy_id,
        command=await template_obj.generate_command(),
        arguments=args,
        input_files=files,
        playbook_id=template_obj.playbook_id,
        socks_server_id=template_obj.socks_server_id,
    )
    return await crud.create_proxy_job(db, proxy_job=job)


@router.post(
    "/playbooks/ai",  # Path as used in the frontend
    response_model=schemas.GeneratedYamlOutput,  # Use the new output schema
    tags=["templates", "ai"],  # Add relevant tags for docs
    summary="Generate Playbook Template YAML from README",
    description="Accepts README markdown content and uses an AI model to generate a playbook template YAML.",
    status_code=status.HTTP_200_OK,  # Explicitly set success code (200 is default for POST often 201, but here we return generated content)
)
async def generate_playbook_template_from_ai(
    input_data: schemas.ReadmeInput,  # Use the new input schema
    # db: AsyncSession = Depends(get_db), # Keep DB if needed for logging or other checks
    user: models.User = Depends(current_active_user),  # Ensure user is authenticated
):
    """
    Receives README content and attempts to generate a playbook YAML using an AI service.
    """
    if not settings.gemini_enabled:
        return Response(
            f"Gemini is not enabled, please configure the gemini api key and set GEMINI_ENABLED=True",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    try:
        # Call the AI generation service function
        generated_yaml = await prompts.generate_playbook_yaml(input_data.readme)

        # The validation is now handled inside generate_playbook_yaml_from_readme
        # If it returns, we assume it's valid enough

        # Return the generated YAML in the expected format
        return schemas.GeneratedYamlOutput(yaml=generated_yaml.yaml_content)

    except Exception as e:
        # Catch any other unexpected errors during the process
        print(f"Unexpected error during AI playbook generation: {e}")
        return Response(
            f"Unexpected error during AI playbook generation",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post(
    "/playbooks/{uuid}",
    response_model=Union[
        schemas.C2Job, schemas.ProxyJob, schemas.ProxyChain, schemas.ErrorResponse
    ],
    tags=["c2", "crud"],
)
async def create_chain_from_template(
    uuid: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    body = await request.json()
    schema = await crud.get_playbook_template(uuid)
    if schema:
        try:
            chain = schemas.PlaybookTemplate(**yaml.safe_load(schema.yaml))
            model = chain.create_model()(**body).model_dump()
        except ValidationError as e:
            return Response(e.json(), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        try:
            return await crud.create_chain_from_template(db, chain, model)
        except ValidationError as e:
            return Response(e.json(), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    else:
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@router.post(
    "/playbooks/",
    response_model=schemas.PlaybookTemplateView,
    tags=["c2", "crud"],
)
async def create_chain_template(
    chain_template: schemas.PlaybookTemplateBase,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    try:
        schema = schemas.PlaybookTemplateCreate(
            **yaml.safe_load(chain_template.yaml), yaml=chain_template.yaml
        )
    except ValidationError as e:
        return Response(e.json(), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except yaml.YAMLError as e:
        return Response(
            f"yaml is invalid: {e}", status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    except TypeError:
        return Response(
            f"yaml is invalid: format is wrong.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    return await crud.create_playbook_template(db, schema)


@router.post(
    "/{c2_type}/{name}",
    response_model=Union[
        schemas.C2Job, schemas.ProxyJob, schemas.ProxyChain, schemas.ErrorResponse
    ],
    tags=["c2", "crud"],
)
async def create_from_template(
    c2_type: schemas.C2Type,
    name: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: models.User = Depends(current_active_user),
):
    body = await request.json()
    try:
        if c2_type == schemas.C2Type.c2:
            template = C2_JOB_BASE_MAP[name]
            return await create_c2_job(db, template, body)
        if c2_type == schemas.C2Type.proxy:
            template = PROXY_JOB_BASE_MAP[name]
            return await create_proxy_job(db, template, body)

    except KeyError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return dict(error="Not found")
    except ValidationError as e:
        return Response(e.json(), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    response.status_code = status.HTTP_400_BAD_REQUEST
    return dict(error="Not found")


add_pagination(router)
