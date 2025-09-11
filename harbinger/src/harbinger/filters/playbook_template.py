from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class PlaybookTemplateFilter(Filter):
    order_by: list[str] | None = ["name"]
    search: str | None = None
    tactic: str | None = None
    technique: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.PlaybookTemplate
        search_model_fields = ["name", "yaml", "tactic", "technique"]

