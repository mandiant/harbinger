from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class ImplantFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))
    c2_server_id: UUID4 | None = None
    host_id: UUID4 | None = None
    hostname: str | None = None
    os: str | None = None
    payload_type: str | None = None
    c2_type: str | None = None
    username: str | None = None
    domain: str | None = None

    class Constants(Filter.Constants):
        model = models.C2Implant
        search_model_fields = ["name", "hostname", "description", "username", "domain"]
