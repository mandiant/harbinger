from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class C2OutputFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    c2_implant_id: UUID4 | None = None 
    c2_server_id: UUID4 | None = None 
    c2_task_id: UUID4 | None = None 
    output_type: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.C2Output
        search_model_fields = ["response_text"]

