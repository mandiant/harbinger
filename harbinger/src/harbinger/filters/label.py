from fastapi_filter.contrib.sqlalchemy import Filter

from harbinger import models


class LabelFilter(Filter):
    id__in: list[str] | None = None
    name__in: list[str] | None = None
    category: str | None = None
    name__not_in: list[str] | None = None

    class Constants(Filter.Constants):
        model = models.Label
