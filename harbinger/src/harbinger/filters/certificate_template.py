from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class CertificateTemplateFilter(Filter): 
    order_by: list[str] | None = ["template_name"]
    search: str | None = None
    template_name: str | None = None
    display_name: str | None = None
    enabled: bool | None = None
    client_authentication: bool | None = None
    enrollment_agent: bool | None = None
    any_purpose: bool | None = None
    enrollee_supplies_subject: bool | None = None
    requires_manager_approval: bool | None = None
    requires_manager_archival: bool | None = None
    authorized_signatures_required: int | None = None
    validity_period: str | None = None
    renewal_period: str | None = None
    minimum_rsa_key_length: int | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.CertificateTemplate
        search_model_fields = ['template_name', 'display_name', 'validity_period', 'renewal_period']

