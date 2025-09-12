from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import UUID4

from harbinger import models

from .label import LabelFilter


class HighlightFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    file_id: str | UUID4 | None = None
    c2_task_id: str | UUID4 | None = None
    c2_task_output_id: str | UUID4 | None = None
    proxy_job_output_id: str | UUID4 | None = None
    proxy_job_id: str | UUID4 | None = None
    parse_result_id: str | UUID4 | None = None
    rule_id: int | None = None
    rule_type: str | None = None
    hit: str | None = None
    start: int | None = None
    end: int | None = None
    line: int | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Highlight
        search_model_fields = ["rule_type", "hit"]
