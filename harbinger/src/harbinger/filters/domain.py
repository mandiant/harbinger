from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class DomainFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    short_name: str | None = None
    long_name: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Domain
        search_model_fields = ["short_name", "long_name"]
