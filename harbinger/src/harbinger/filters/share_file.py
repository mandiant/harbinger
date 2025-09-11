from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class ShareFileFilter(Filter): 
    order_by: list[str] | None = ["-time_created"]
    search: str | None = None
    type: str | None = None
    file_id: str | UUID4 | None = None
    parent_id: str | UUID4 | None = None
    share_id: str | UUID4 | None = None
    unc_path: str | None = None
    depth: int | None = None
    name: str | None = None
    downloaded: bool | None = None
    indexed: bool | None = None
    extension: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.ShareFile
        search_model_fields = ['type', 'unc_path', 'name']

