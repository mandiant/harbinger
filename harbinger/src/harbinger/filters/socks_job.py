from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from harbinger import models

from .label import LabelFilter


class SocksJobFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    command: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))
    status: str | None = None
    processing_status: str | None = None

    class Constants(Filter.Constants):
        model = models.ProxyJob
        search_model_fields = ["command", "arguments"]
