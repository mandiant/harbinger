from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import UUID4

from harbinger import models

from .label import LabelFilter


class PlaybookFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    playbook_name: str | None = None
    description: str | None = None
    status: str | None = None
    steps: int | None = None
    completed: int | None = None
    playbook_template_id: str | UUID4 | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Playbook
        search_model_fields = ["playbook_name", "description", "status"]
