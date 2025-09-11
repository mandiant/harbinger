from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class C2ServerFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    type: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.C2Server
        search_model_fields = ["name", "hostname", "username"]
