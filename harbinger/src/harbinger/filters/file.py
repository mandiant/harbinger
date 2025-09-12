from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import UUID4

from harbinger import models

from .label import LabelFilter


class FileFilter(Filter):
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    filetype: str | None = None
    job_id: str | UUID4 | None = None
    manual_timeline_task_id: str | UUID4 | None = None
    c2_task_id: str | UUID4 | None = None
    c2_implant_id: str | UUID4 | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.File
        search_model_fields = [
            "filename",
            "path",
            "filetype",
            "magic_mimetype",
            "magika_mimetype",
        ]
