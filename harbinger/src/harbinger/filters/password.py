from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter

from harbinger import models

from .label import LabelFilter


class PasswordFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    password: str | None = None
    nt: str | None = None
    aes256_key: str | None = None
    aes128_key: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.Password
        search_model_fields = ["password", "nt", "aes256_key", "aes128_key"]
