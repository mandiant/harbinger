from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class ShareFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))
    host_id: str | None = None

    class Constants(Filter.Constants):
        model = models.Share
        search_model_fields = ["name", "unc_path", "remark"]
