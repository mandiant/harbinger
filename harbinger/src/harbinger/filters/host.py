from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from harbinger import models

from .label import LabelFilter


class HostFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    hostname: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Host
        search_model_fields = ["name", "objectid", "fqdn"]
