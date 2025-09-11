from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4


class SituationalAwarenessFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    name: str | None = None
    category: str | None = None
    domain_id: str | UUID4 | None = None

    class Constants(Filter.Constants):
        model = models.SituationalAwareness
        search_model_fields = ['name', 'category', 'value_string']

