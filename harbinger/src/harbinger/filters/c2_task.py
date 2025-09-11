from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class C2TaskFilter(Filter):
    order_by: list[str] | None = ["-time_completed"]
    search: str | None = None
    c2_implant_id: str | UUID4 | None = None
    status: str | None = None
    command_name: str | None = None
    operator: str | None = None
    processing_status: str | None = None
    internal_id: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.C2Task
        search_model_fields = ["original_params", "display_params", "command_name"]
