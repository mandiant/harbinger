from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import UUID4

from harbinger import models

from .label import LabelFilter


class ChecklistFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    domain_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    phase: str | None = None
    name: str | None = None
    status: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Checklist
        search_model_fields = ["phase", "name", "status"]
