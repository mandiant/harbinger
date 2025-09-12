from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import UUID4

from harbinger import models


class LlmLogFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    plan_id: str | UUID4 | None = None
    log_type: str | None = None

    class Constants(Filter.Constants):
        model = models.LlmLog
        search_model_fields = ["log_type"]
