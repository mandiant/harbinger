from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4


class TimeLineFilter(Filter):
    order_by: list[str] | None = ["-time_completed"]
    search: str | None = None
    status: str | None = None

    class Constants(Filter.Constants):
        model = models.TimeLine
        search_model_fields = ["status"]
