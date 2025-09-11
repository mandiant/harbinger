from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class PlanFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    name: str | None = None
    objective: str | None = None
    status: str | None = None
    llm_status: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Plan
        search_model_fields = ["name", "objective", "status"]
