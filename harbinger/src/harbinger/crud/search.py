from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query, selectinload

from harbinger import filters as ft
from harbinger import models

# This registry maps models to their filters and frontend URL prefixes.
# The `url_prefix` is derived directly from the Vue router configuration.
SEARCHABLE_MODELS = [
    {
        "model": models.Host,
        "filter": ft.HostFilter,
        "name_field": "name",
        "context_field": "fqdn",
        "url_prefix": "/hosts/",
    },
    {
        "model": models.File,
        "filter": ft.FileFilter,
        "name_field": "filename",
        "context_field": "path",
        "url_prefix": "/files/",
    },
    {
        "model": models.Credential,
        "filter": ft.CredentialFilter,
        "name_field": "username",
        "context_field": "domain.long_name",
        "url_prefix": "/credentials/",
        "options": [selectinload(models.Credential.domain)],
    },
    {
        "model": models.Playbook,
        "filter": ft.PlaybookFilter,
        "name_field": "playbook_name",
        "context_field": "description",
        "url_prefix": "/playbooks/",
    },
    {
        "model": models.C2Implant,
        "filter": ft.ImplantFilter,
        "name_field": "name",
        "context_field": "hostname",
        "url_prefix": "/implants/",
    },
    {
        "model": models.C2Server,
        "filter": ft.C2ServerFilter,
        "name_field": "name",
        "context_field": "hostname",
        "url_prefix": "/servers/",
    },
    {
        "model": models.Share,
        "filter": ft.ShareFilter,
        "name_field": "name",
        "context_field": "unc_path",
        "url_prefix": "/shares/",
    },
    {
        "model": models.Issue,
        "filter": ft.IssueFilter,
        "name_field": "name",
        "context_field": "description",
        "url_prefix": "/issues/",
    },
    {
        "model": models.Plan,
        "filter": ft.PlanFilter,
        "name_field": "name",
        "context_field": "objective",
        "url_prefix": "/plans/",
    },
    {
        "model": models.Suggestion,
        "filter": ft.SuggestionFilter,
        "name_field": "name",
        "context_field": "reason",
        "url_prefix": "/suggestions/",
    },
    {
        "model": models.ProxyJob,
        "filter": ft.SocksJobFilter,
        "name_field": "command",
        "context_field": "arguments",
        "url_prefix": "/proxy_jobs/",
    },
    {
        "model": models.C2Task,
        "filter": ft.C2TaskFilter,
        "name_field": "command_name",
        "context_field": "display_params",
        "url_prefix": "/tasks/",
    },
    {
        "model": models.C2Output,
        "filter": ft.C2OutputFilter,
        "name_field": "response_text",
        "context_field": "output_type",
        "url_prefix": "/c2/output/",
    },
]


async def _search_model(db: AsyncSession, query: str, config: dict):
    """Searches a single model using its filter class."""
    results = []
    model_filter = config["filter"](search=query)

    query_stmt = select(config["model"])

    # Add any specific relationship loading options
    if "options" in config:
        for option in config["options"]:
            query_stmt = query_stmt.options(option)

    filtered_query: Query = model_filter.filter(query_stmt)
    query_result = await db.execute(filtered_query.limit(10))  # Limit results per model
    db_objects = query_result.unique().scalars().all()

    for obj in db_objects:
        context_value = None
        if config["context_field"]:
            # Handle nested attributes like "domain.long_name"
            context_attr = config["context_field"].split(".")
            context_obj = obj
            for attr in context_attr:
                if hasattr(context_obj, attr):
                    context_obj = getattr(context_obj, attr)
                else:
                    context_obj = None
                    break
            context_value = str(context_obj) if context_obj is not None else None

        results.append(
            {
                "id": obj.id,
                "type": config["model"].__name__,
                "name": getattr(obj, config["name_field"]) or "",
                "context": context_value,
                "url": f"{config['url_prefix']}{obj.id}",
            }
        )
    return results


async def perform_global_search(db: AsyncSession, query: str) -> list:
    """
    Asynchronously searches all registered models and aggregates the results.
    """
    all_results = []
    for model_config in SEARCHABLE_MODELS:
        results = await _search_model(db=db, query=query, config=model_config)
        all_results.extend(results)
    return all_results
