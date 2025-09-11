from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class ProxyFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    host: str | None = None
    port: int | None = None
    type: str | None = None
    status: str | None = None
    note: str | None = None
    remote_hostname: str | None = None
    username: str | None = None
    password: str | None = None
    c2_server_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    c2_task_id: str | UUID4 | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Proxy
        search_model_fields = ['host', 'type', 'status', 'note', 'remote_hostname']

