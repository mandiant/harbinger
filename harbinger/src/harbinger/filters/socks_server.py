from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class SocksServerFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    operating_system: str | None = None
    type: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))
    status: str | None = None

    class Constants(Filter.Constants):
        model = models.SocksServer
        search_model_fields = ["type", "hostname", "operating_system"]
