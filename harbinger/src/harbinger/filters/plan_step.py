from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class PlanStepFilter(Filter): 
    order_by: list[str] | None = ["order"]
    search: str | None = None
    id__in: list[UUID4] | None = None
    plan_id: str | UUID4 | None = None
    description: str | None = None
    status: str | None = None
    llm_status: str | None = None
    order: int | None = None
    notes: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.PlanStep
        search_model_fields = ['description', 'status', 'notes']

# Filters.py