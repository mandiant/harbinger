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

from pydantic import BaseModel, Field, AliasChoices, RootModel
from typing import Optional, Any, Union

class EnrollmentPermissions(BaseModel):
    enrollment_rights: list[str] = Field(
        validation_alias=AliasChoices("Enrollment Rights")
    )


class ObjectControlPermissions(BaseModel):
    owner: str = Field(validation_alias=AliasChoices("Owner"))
    full_control_principals: list[str] | None = Field(
        validation_alias=AliasChoices("Full Control Principals"), default=[]
    )
    write_owner_principals: list[str] | None = Field(
        validation_alias=AliasChoices("Write Owner Principals"), default=[]
    )
    write_dacl_principals: list[str] | None = Field(
        validation_alias=AliasChoices("Write Dacl Principals"), default=[]
    )
    write_property_principals: list[str] | None = Field(
        validation_alias=AliasChoices("Write Property Principals"), default=[]
    )


class Permissions(BaseModel):
    enrollment_permissions: EnrollmentPermissions = Field(
        validation_alias=AliasChoices("Enrollment Permissions")
    )
    object_control_permissions: ObjectControlPermissions = Field(
        validation_alias=AliasChoices("Object Control Permissions")
    )


class CertificateAuthority(BaseModel):
    ca_name: str = Field(validation_alias=AliasChoices("CA Name"))
    dns_name: str = Field(validation_alias=AliasChoices("DNS Name"))
    certificate_subject: str = Field(
        validation_alias=AliasChoices("Certificate Subject")
    )
    certificate_serial_number: str = Field(
        validation_alias=AliasChoices("Certificate Serial Number")
    )
    certificate_validity_start: str = Field(
        validation_alias=AliasChoices("Certificate Validity Start")
    )
    certificate_validity_end: str = Field(
        validation_alias=AliasChoices("Certificate Validity End")
    )
    web_enrollment: str = Field(validation_alias=AliasChoices("Web Enrollment"))
    user_specified_san: str = Field(validation_alias=AliasChoices("User Specified SAN"))
    request_disposition: str = Field(
        validation_alias=AliasChoices("Request Disposition")
    )
    enforce_encryption_for_requests: str = Field(
        validation_alias=AliasChoices("Enforce Encryption for Requests")
    )


CertificateAuthorities = RootModel[dict[int, CertificateAuthority]]


Vulnerabilities = RootModel[dict[str, str]]


class CertificateTemplate(BaseModel):
    template_name: str = Field(validation_alias=AliasChoices("Template Name"))
    display_name: str = Field(validation_alias=AliasChoices("Display Name"))
    certificate_authorities: list[str] | None = Field(
        validation_alias=AliasChoices("Certificate Authorities"), default=[]
    )
    enabled: bool = Field(validation_alias=AliasChoices("Enabled"))
    client_authentication: bool = Field(
        validation_alias=AliasChoices("Client Authentication")
    )
    enrollment_agent: bool = Field(validation_alias=AliasChoices("Enrollment Agent"))
    any_purpose: bool = Field(validation_alias=AliasChoices("Any Purpose"))
    enrollee_supplies_subject: bool = Field(
        validation_alias=AliasChoices("Enrollee Supplies Subject")
    )
    certificate_name_flag: list[str] = Field(
        validation_alias=AliasChoices("Certificate Name Flag")
    )
    enrollment_flag: list[str] = Field(validation_alias=AliasChoices("Enrollment Flag"))
    private_key_flag: list[str] = Field(
        validation_alias=AliasChoices("Private Key Flag")
    )
    extended_key_usage: list[str] | None = Field(
        validation_alias=AliasChoices("Extended Key Usage"), default=[]
    )
    requires_manager_approval: bool = Field(
        validation_alias=AliasChoices("Requires Manager Approval")
    )
    requires_manager_archival: bool = Field(
        validation_alias=AliasChoices("Requires Key Archival")
    )
    authorized_signatures_required: int = Field(
        validation_alias=AliasChoices("Authorized Signatures Required")
    )
    validity_period: str = Field(validation_alias=AliasChoices("Validity Period"))
    renewal_period: str = Field(validation_alias=AliasChoices("Renewal Period"))
    minimum_rsa_key_length: int = Field(
        validation_alias=AliasChoices("Minimum RSA Key Length")
    )
    permissions: Permissions = Field(validation_alias=AliasChoices("Permissions"))
    vulnerabilities: Vulnerabilities | None = Field(
        validation_alias=AliasChoices("[!] Vulnerabilities"), default=None
    )


CertificateTemplates = RootModel[dict[int, CertificateTemplate]]


class CertipyJson(BaseModel):
    certificate_authorities: CertificateAuthorities = Field(
        validation_alias=AliasChoices(
            "certificate_authorities", "Certificate Authorities"
        )
    )
    certificate_templates: CertificateTemplates = Field(
        validation_alias=AliasChoices("certificate_templates", "Certificate Templates")
    )


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
    certificates: list[CertifyCertificate] = Field(validation_alias=AliasChoices("Certificates"))
    templates: list[str] = Field(validation_alias=AliasChoices("Templates"))
    editf_attributesubjectaltname2: bool = Field(validation_alias=AliasChoices("EDITF_ATTRIBUTESUBJECTALTNAME2"))
    acl: CertifyAcl = Field(validation_alias=AliasChoices("ACL"))
    enrollment_agent_restrictions: Optional[Any] = Field(validation_alias=AliasChoices("EnrollmentAgentRestrictions"))

class CertifyOid(BaseModel): 
    value: str = Field(validation_alias=AliasChoices("Value"))
    friendly_name: Optional[Any] = Field(validation_alias=AliasChoices("FriendlyName"))

class CertifyCertificateTemplate(BaseModel): 
    template_name: str = Field(validation_alias=AliasChoices("Name"))
    domain_name: str = Field(validation_alias=AliasChoices("DomainName"))
    display_name: str = Field(validation_alias=AliasChoices("DisplayName"))
    guid: str = Field(validation_alias=AliasChoices("Guid"))
    schema_version: Optional[Any] = Field(validation_alias=AliasChoices("SchemaVersion"))
    validity_period: str = Field(validation_alias=AliasChoices("ValidityPeriod"))
    renewal_period: str = Field(validation_alias=AliasChoices("RenewalPeriod"))
    oid: CertifyOid = Field(validation_alias=AliasChoices("Oid"))
    certificate_name_flag: int = Field(validation_alias=AliasChoices("CertificateNameFlag"))
    enrollment_flag: int = Field(validation_alias=AliasChoices("EnrollmentFlag"))
    extended_key_usage: list[str] | None = Field(validation_alias=AliasChoices("ExtendedKeyUsage"), default=[])
    authorized_signatures_required: int = Field(validation_alias=AliasChoices("AuthorizedSignatures"))
    application_policies: Optional[Any] = Field(validation_alias=AliasChoices("ApplicationPolicies"))
    issuance_policies: Optional[Any] = Field(validation_alias=AliasChoices("IssuancePolicies"))
    certificate_application_policies: Optional[Union[list[str], Any]] = Field(validation_alias=AliasChoices("CertificateApplicationPolicies"))
    requires_manager_approval: bool = Field(validation_alias=AliasChoices("RequiresManagerApproval"))
    enrollee_supplies_subject: bool = Field(validation_alias=AliasChoices("EnrolleeSuppliesSubject"))
    acl: CertifyAcl = Field(validation_alias=AliasChoices("ACL"))

class CertifyMeta(BaseModel): 
    type: str = Field(validation_alias=AliasChoices("type"))
    count: int = Field(validation_alias=AliasChoices("count"))
    version: int = Field(validation_alias=AliasChoices("version"))

class CertifyRoot(BaseModel): 
    certificate_authorities: list[CertifyCertificateAuthority] | None = Field(validation_alias=AliasChoices("CertificateAuthorities"), default=None)
    certificate_templates: list[CertifyCertificateTemplate] | None = Field(validation_alias=AliasChoices("CertificateTemplates"), default=None)
    meta: CertifyMeta = Field(validation_alias=AliasChoices("Meta"))
