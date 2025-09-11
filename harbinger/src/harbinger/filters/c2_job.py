from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class C2JobFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    status: str | None = None
    c2_type: str | None = None
    c2_task_id: str | UUID4 | None = None
    c2_server_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    command: str | None = None
    arguments: str | None = None
    playbook_id: str | UUID4 | None = None
    message: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.C2Job
        search_model_fields = ['status', 'c2_type', 'command', 'arguments', 'message']

