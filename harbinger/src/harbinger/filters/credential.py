from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import UUID4

from harbinger import models

from .domain import DomainFilter
from .label import LabelFilter


class CredentialFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    domain_id: str | UUID4 | None = None
    username: str | None = None
    password_id: str | UUID4 | None = None
    kerberos_id: str | UUID4 | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))
    domain: DomainFilter | None = FilterDepends(with_prefix("domain", DomainFilter))

    class Constants(Filter.Constants):
        model = models.Credential
        search_model_fields = ["username"]
