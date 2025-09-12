from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from harbinger import models

from .label import LabelFilter


class ObjectivesFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Objectives
        search_model_fields = ["name", "description", "status"]
