# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
from pydantic import (
    BaseModel,
    Field,
    AliasChoices,
    RootModel,
    field_validator,
    FieldValidationInfo,
)
from typing import Optional, Any, Union


# --- Main Models ---
class CertificateAuthority(BaseModel):
    ca_name: str = Field(alias="CA Name")
    dns_name: str = Field(alias="DNS Name")
    certificate_subject: str = Field(alias="Certificate Subject")
    certificate_serial_number: str = Field(alias="Certificate Serial Number")
    certificate_validity_start: str = Field(alias="Certificate Validity Start")
    certificate_validity_end: str = Field(alias="Certificate Validity End")
    web_enrollment: Optional[str] = Field(alias="Web Enrollment", default=None)
    user_specified_san: str = Field(alias="User Specified SAN")
    request_disposition: str = Field(alias="Request Disposition")
    enforce_encryption_for_requests: str = Field(
        alias="Enforce Encryption for Requests"
    )

    @field_validator("web_enrollment", mode="before")
    @classmethod
    def convert_web_enrollment_dict_to_json_string(cls, v: Any) -> Optional[str]:
        """
        If the input 'v' for web_enrollment is a dictionary,
        convert it to a JSON string. Otherwise, pass it through
        (Pydantic will then validate if it's a string or None).
        """
        if isinstance(v, dict):
            return json.dumps(v)
        return v

    class Config:
        populate_by_name = True


class CertificateAuthorities(RootModel[dict[str, CertificateAuthority]]):
    root: dict[str, CertificateAuthority]


class Vulnerabilities(RootModel[dict[str, str]]):
    """
    Represents a dictionary where keys are vulnerability names (strings)
    and values are descriptions (strings).
    """

    root: dict[str, str]


# Placeholder for the Permissions model - its actual structure depends on your JSON
class EnrollmentPermissions(BaseModel):
    enrollment_rights: Optional[list[str]] = Field(
        alias="Enrollment Rights", default=None
    )


class ObjectControlPermissions(BaseModel):
    owner: Optional[str] = Field(alias="Owner", default=None)
    full_control_principals: Optional[list[str]] = Field(
        alias="Full Control Principals", default_factory=list
    )
    write_owner_principals: Optional[list[str]] = Field(
        alias="Write Owner Principals", default_factory=list
    )
    write_dacl_principals: Optional[list[str]] = Field(
        alias="Write Dacl Principals", default_factory=list
    )
    write_property_auto_enroll: Optional[list[str]] = Field(
        alias="Write Property AutoEnroll", default_factory=list
    )
    write_property_principals: Optional[list[str]] = Field(
        alias="Write Property Enroll", default_factory=list
    )


class Permissions(BaseModel):
    enrollment_permissions: Optional[EnrollmentPermissions] = Field(
        alias="Enrollment Permissions", default=None
    )
    object_control_permissions: Optional[ObjectControlPermissions] = Field(
        alias="Object Control Permissions", default=None
    )


class CertificateTemplate(BaseModel):
    template_name: str = Field(alias="Template Name")
    display_name: str = Field(alias="Display Name")
    certificate_authorities: Optional[list[str]] = Field(
        alias="Certificate Authorities", default=None
    )
    enabled: bool = Field(alias="Enabled")
    client_authentication: bool = Field(alias="Client Authentication")
    enrollment_agent: bool = Field(alias="Enrollment Agent")
    any_purpose: bool = Field(alias="Any Purpose")
    enrollee_supplies_subject: bool = Field(alias="Enrollee Supplies Subject")
    certificate_name_flag: Optional[list[int]] = Field(
        alias="Certificate Name Flag", default=None
    )
    enrollment_flag: Optional[list[int]] = Field(alias="Enrollment Flag", default=None)
    private_key_flag: Optional[list[int]] = Field(
        alias="Private Key Flag", default=None
    )
    extended_key_usage: Optional[list[str]] = Field(
        alias="Extended Key Usage", default=None
    )
    requires_manager_approval: bool = Field(alias="Requires Manager Approval")
    requires_key_archival: bool = Field(alias="Requires Key Archival")
    authorized_signatures_required: int = Field(alias="Authorized Signatures Required")
    schema_version: Optional[int] = Field(
        alias="Schema Version", default=None
    )  # Made optional for safety
    validity_period: str = Field(alias="Validity Period", default='')
    renewal_period: str = Field(alias="Renewal Period", default='')
    minimum_rsa_key_length: int = Field(alias="Minimum RSA Key Length", default=0)
    permissions: Optional[Permissions] = Field(alias="Permissions", default=None)
    vulnerabilities: Optional[Vulnerabilities] = Field(
        alias="[!] Vulnerabilities", default=None
    )
    template_created: Optional[str] = Field(alias="Template Created", default=None)
    template_last_modified: Optional[str] = Field(
        alias="Template Last Modified", default=None
    )
    ra_application_policies: Optional[list[str]] = Field(
        alias="RA Application Policies", default=None
    )
    user_enrollable_principals: Optional[list[str]] = Field(
        alias="[+] User Enrollable Principals", default=None
    )
    remarks: Optional[dict[str, str]] = Field(alias="[*] Remarks", default=None)

    class Config:
        populate_by_name = True


class CertificateTemplates(RootModel[dict[str, CertificateTemplate]]):
    root: dict[str, CertificateTemplate]


class CertipyJson(BaseModel):
    certificate_authorities: CertificateAuthorities = Field(
        alias="Certificate Authorities"
    )
    certificate_templates: CertificateTemplates = Field(
        alias="Certificate Templates"
    )

    class Config:
        populate_by_name = True

    @field_validator("certificate_authorities", "certificate_templates", mode="before")
    @classmethod
    def handle_string_error_for_root_model_dicts(
        cls, v: Any, info: FieldValidationInfo
    ) -> Any:
        """
        If the input 'v' for fields expecting RootModel[dict[...]] is a string (error message),
        return an empty dictionary to allow parsing of other fields.
        Otherwise, pass it through for normal Pydantic parsing.
        """
        if isinstance(v, str):
            return {}  # Return an empty dict, Pydantic will create an empty RootModel
        return v


class CertifyCertificate(BaseModel):
    subject_name: str = Field(validation_alias=AliasChoices("SubjectName"))
    thumbprint: str = Field(validation_alias=AliasChoices("Thumbprint"))
    serial: str = Field(validation_alias=AliasChoices("Serial"))
    start_date: str = Field(validation_alias=AliasChoices("StartDate"))
    end_date: str = Field(validation_alias=AliasChoices("EndDate"))
    cert_chain: list[str] = Field(validation_alias=AliasChoices("CertChain"))


class CertifyAce(BaseModel):
    type: str = Field(validation_alias=AliasChoices("Type"))
    rights: str = Field(validation_alias=AliasChoices("Rights"))
    principal: str = Field(validation_alias=AliasChoices("Principal"))


class CertifyAcl(BaseModel):
    owner: str = Field(validation_alias=AliasChoices("Owner"))
    aces: list[CertifyAce] = Field(validation_alias=AliasChoices("ACEs"))


class CertifyCertificateAuthority(BaseModel):
    ca_name: str = Field(validation_alias=AliasChoices("Name"))
    dns_name: str = Field(validation_alias=AliasChoices("DnsHostname"))
    domain_name: str = Field(validation_alias=AliasChoices("DomainName"))
    guid: str = Field(validation_alias=AliasChoices("Guid"))
    flags: str = Field(validation_alias=AliasChoices("Flags"))
    certificates: list[CertifyCertificate] = Field(
        validation_alias=AliasChoices("Certificates")
    )
    templates: list[str] = Field(validation_alias=AliasChoices("Templates"))
    editf_attributesubjectaltname2: bool = Field(
        validation_alias=AliasChoices("EDITF_ATTRIBUTESUBJECTALTNAME2")
    )
    acl: CertifyAcl = Field(validation_alias=AliasChoices("ACL"))
    enrollment_agent_restrictions: Optional[Any] = Field(
        validation_alias=AliasChoices("EnrollmentAgentRestrictions")
    )


class CertifyOid(BaseModel):
    value: str = Field(validation_alias=AliasChoices("Value"))
    friendly_name: Optional[Any] = Field(validation_alias=AliasChoices("FriendlyName"))


class CertifyCertificateTemplate(BaseModel):
    template_name: str = Field(validation_alias=AliasChoices("Name"))
    domain_name: str = Field(validation_alias=AliasChoices("DomainName"))
    display_name: str = Field(validation_alias=AliasChoices("DisplayName"))
    guid: str = Field(validation_alias=AliasChoices("Guid"))
    schema_version: Optional[Any] = Field(
        validation_alias=AliasChoices("SchemaVersion")
    )
    validity_period: str = Field(validation_alias=AliasChoices("ValidityPeriod"))
    renewal_period: str = Field(validation_alias=AliasChoices("RenewalPeriod"))
    oid: CertifyOid = Field(validation_alias=AliasChoices("Oid"))
    certificate_name_flag: int = Field(
        validation_alias=AliasChoices("CertificateNameFlag")
    )
    enrollment_flag: int = Field(validation_alias=AliasChoices("EnrollmentFlag"))
    extended_key_usage: list[str] | None = Field(
        validation_alias=AliasChoices("ExtendedKeyUsage"), default=[]
    )
    authorized_signatures_required: int = Field(
        validation_alias=AliasChoices("AuthorizedSignatures")
    )
    application_policies: Optional[Any] = Field(
        validation_alias=AliasChoices("ApplicationPolicies")
    )
    issuance_policies: Optional[Any] = Field(
        validation_alias=AliasChoices("IssuancePolicies")
    )
    certificate_application_policies: Optional[Union[list[str], Any]] = Field(
        validation_alias=AliasChoices("CertificateApplicationPolicies")
    )
    requires_manager_approval: bool = Field(
        validation_alias=AliasChoices("RequiresManagerApproval")
    )
    enrollee_supplies_subject: bool = Field(
        validation_alias=AliasChoices("EnrolleeSuppliesSubject")
    )
    acl: CertifyAcl = Field(validation_alias=AliasChoices("ACL"))


class CertifyMeta(BaseModel):
    type: str = Field(validation_alias=AliasChoices("type"))
    count: int = Field(validation_alias=AliasChoices("count"))
    version: int = Field(validation_alias=AliasChoices("version"))


class CertifyRoot(BaseModel):
    certificate_authorities: list[CertifyCertificateAuthority] | None = Field(
        validation_alias=AliasChoices("CertificateAuthorities"), default=None
    )
    certificate_templates: list[CertifyCertificateTemplate] | None = Field(
        validation_alias=AliasChoices("CertificateTemplates"), default=None
    )
    meta: CertifyMeta = Field(validation_alias=AliasChoices("Meta"))
