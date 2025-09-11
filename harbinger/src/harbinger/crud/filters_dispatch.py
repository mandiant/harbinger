from harbinger import schemas
from harbinger import filters
from sqlalchemy.ext.asyncio import AsyncSession

from .action import get_action_filters
from .c2_implant import get_c2_implant_filters
from .c2_job import get_c2_jobs_filters
from .c2_output import get_c2_output_filters
from .c2_server import get_c2_servers_filters
from .c2_task import get_c2_task_filters
from .certificate_authority import get_certificate_authorities_filters
from .certificate_template import get_certificate_templates_filters
from .checklist import get_checklists_filters
from .credential import get_credentials_filters
from .domain import get_domains_filters
from .file import get_file_filters, get_share_file_filters
from .highlight import get_highlights_filters
from .host import get_host_filters
from .issue import get_issue_filters
from .objective import get_objectives_filters
from .playbook import get_playbook_template_filters, get_playbooks_filters
from .proxy import get_proxy_filters
from .share import get_share_filters
from .situational_awareness import get_situational_awarenesss_filters
from .socks_server import get_socks_job_filters, get_socks_server_filters
from .suggestion import get_suggestions_filters
from .timeline import get_timeline_filters


async def get_filters_for_model(
    db: AsyncSession, model_name: str
) -> list[schemas.Filter]:
    """
    Returns a list of filters for a given model.
    """
    filter_map = {
        "action": (get_action_filters, filters.ActionFilter),
        "c2_implant": (get_c2_implant_filters, filters.ImplantFilter),
        "c2_job": (get_c2_jobs_filters, filters.C2JobFilter),
        "c2_output": (get_c2_output_filters, filters.C2OutputFilter),
        "c2_server": (get_c2_servers_filters, filters.C2ServerFilter),
        "c2_task": (get_c2_task_filters, filters.C2TaskFilter),
        "certificate_authority": (
            get_certificate_authorities_filters,
            filters.CertificateAuthorityFilter,
        ),
        "certificate_template": (
            get_certificate_templates_filters,
            filters.CertificateTemplateFilter,
        ),
        "checklist": (get_checklists_filters, filters.ChecklistFilter),
        "credential": (get_credentials_filters, filters.CredentialFilter),
        "domain": (get_domains_filters, filters.DomainFilter),
        "file": (get_file_filters, filters.FileFilter),
        "highlight": (get_highlights_filters, filters.HighlightFilter),
        "host": (get_host_filters, filters.HostFilter),
        "issue": (get_issue_filters, filters.IssueFilter),
        "objective": (get_objectives_filters, filters.ObjectivesFilter),
        "playbook": (get_playbooks_filters, filters.PlaybookFilter),
        "playbook_template": (
            get_playbook_template_filters,
            filters.PlaybookTemplateFilter,
        ),
        "proxy": (get_proxy_filters, filters.ProxyFilter),
        "share": (get_share_filters, filters.ShareFilter),
        "share_file": (get_share_file_filters, filters.ShareFileFilter),
        "situational_awareness": (
            get_situational_awarenesss_filters,
            filters.SituationalAwarenessFilter,
        ),
        "socks_job": (get_socks_job_filters, filters.SocksJobFilter),
        "socks_server": (get_socks_server_filters, filters.SocksServerFilter),
        "suggestion": (get_suggestions_filters, filters.SuggestionFilter),
        "timeline": (get_timeline_filters, filters.TimeLineFilter),
    }
    if model_name not in filter_map:
        raise ValueError(f"Unknown model name: {model_name}")
    filter_func, filter_class = filter_map[model_name]
    filter_instance = filter_class()
    return await filter_func(db, filter_instance)
