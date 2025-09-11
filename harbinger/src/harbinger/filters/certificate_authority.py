from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from harbinger import models
from pydantic import UUID4
from .label import LabelFilter


class CertificateAuthorityFilter(Filter): 
    order_by: list[str] | None = ["ca_name"]
    search: str | None = None
    ca_name: str | None = None
    dns_name: str | None = None
    certificate_subject: str | None = None
    certificate_serial_number: str | None = None
    certificate_validity_start: str | None = None
    certificate_validity_end: str | None = None
    web_enrollment: str | None = None
    user_specified_san: str | None = None
    request_disposition: str | None = None
    enforce_encryption_for_requests: str | None = None
    labels: LabelFilter | None = FilterDepends(with_prefix("label", LabelFilter))

    class Constants(Filter.Constants):
        model = models.CertificateAuthority
        search_model_fields = ['ca_name', 'dns_name', 'certificate_subject', 'certificate_serial_number', 'certificate_validity_start', 'certificate_validity_end', 'web_enrollment', 'user_specified_san', 'request_disposition', 'enforce_encryption_for_requests']

