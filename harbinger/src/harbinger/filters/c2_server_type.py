from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4


class C2ServerTypeFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    name: str | None = None

    class Constants(Filter.Constants):
        model = models.C2ServerType
        search_model_fields = ['name']

