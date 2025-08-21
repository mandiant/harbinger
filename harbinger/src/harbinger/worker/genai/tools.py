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
from harbinger.database import crud, schemas, filters
from harbinger.database.database import SessionLocal
import structlog
from harbinger.config import get_settings
import rigging as rg

import typing as t
from typing import List, Optional, Dict, Any, Iterable
from harbinger.enums import PlanStepStatus
from harbinger.graph import crud as graph_crud
from harbinger.graph.database import get_async_neo4j_session_context


settings = get_settings()

log = structlog.get_logger()


def dict_to_string(data: Dict[str, Any]) -> str:
    return str(data)


def sequence_to_string_list(sequence: Iterable, schema_class: Any) -> List[str]:
    return [str(obj.__dict__) for obj in sequence]


# --- Rigging Tools with Filters ---


@rg.tool
async def get_all_c2_implant_info() -> List[str]:
    """
    Retrieves information for all ACTIVE C2 implants. Implants labeled "Dead" are automatically excluded.
    Each implant's information includes its associated labels. This tool is useful
    for getting a list of viable implants to target.
    Returns:
        A list of string representations for each active implant's information.
    """
    async with SessionLocal() as db:
        # Filter out implants with the "Dead" label.
        # The label ID for "Dead" is d734d03b-50d4-43e3-bb0e-e6bf56ec76b1
        implants = await crud.get_c2_implants(db, not_labels=["Dead"], limit=1000)
        
        if not implants:
            return ["No active C2 implants found."]
        
        implants_list = []
        for implant in implants:
            labels = await crud.recurse_labels_c2_implant(db, implant.id)
            c2_implant_dict = schemas.C2Implant.model_validate(implant).model_dump()
            c2_implant_dict["labels"] = [schemas.Label.model_validate(l).model_dump() for l in labels]
            implants_list.append(json.dumps(c2_implant_dict, default=str))
            
        return implants_list


@rg.tool
async def get_c2_tasks_executed(
    c2_implant_id: Optional[str] = None,
    include_output: bool = False,
    search: Optional[str] = None,
    labels_id__in: Optional[List[str]] = None,
    labels_name__in: Optional[List[str]] = None,
    labels_category: Optional[str] = None,
) -> List[str]:
    """
    Retrieves C2 tasks executed, optionally for a specific implant and including task output,
    with various filtering options. This tool helps to understand command execution history.
    Args:
        c2_implant_id: The ID of the C2 implant to filter tasks by.
        include_output: Whether to include the task output in the retrieved data.
                        Set to True to get the command's results.
        search: A general search string to apply across relevant task fields (original_params, display_params, command_name).
                Use single argument query only, OR/AND/NOT is not supported.
        labels_id__in: List of label IDs to include tasks by.
        labels_name__in: List of label names to include tasks by.
        labels_category: Category of labels to include tasks by.
    Returns:
        A list of string representations for each executed task.
    """
    async with SessionLocal() as db:
        task_filter = filters.C2TaskFilter(
            search=search,
            c2_implant_id=c2_implant_id,
        )
        if labels_id__in or labels_name__in or labels_category:
            task_filter.labels = filters.LabelFilter(
                id__in=labels_id__in,
                name__in=labels_name__in,
                category=labels_category,
            )

        tasks = await crud.get_c2_tasks(db, task_filter, limit=10000)
        if not tasks:
            return ["No C2 tasks found matching the criteria."]
        tasks_executed = []
        for task in tasks:
            task_dict = task.__dict__
            if include_output:
                # Assuming task.id is convertible to UUID4 for the filter
                output_filter = filters.C2OutputFilter(c2_task_id=task.id)
                output = await crud.get_c2_task_output(db, output_filter)
                task_output = "".join([o.response_text for o in output])
                if len(task_output) > 1000:
                    task_output = task_output[0:500] + "..." + task_output[-500:]
                task_dict["task_output"] = task_output
            tasks_executed.append(dict_to_string(task_dict))
        return tasks_executed


@rg.tool
async def get_playbooks(
    search: Optional[str] = None,
    labels_id__in: Optional[List[str]] = None,
    labels_name__in: Optional[List[str]] = None,
    labels_category: Optional[str] = None,
) -> List[str]:
    """
    Retrieves a list of all available playbooks, with various filtering options.
    Playbooks represent automated sequences of actions.
    Args:
        search: A general search string to apply across relevant playbook fields (playbook_name, description, status).
                Use single argument query only, OR/AND/NOT is not supported.
        labels_id__in: List of label IDs to include playbooks by.
        labels_name__in: List of label names to include playbooks by.
        labels_category: Category of labels to include playbooks by.
        labels_name__not_in: List of label names to exclude playbooks by.
    Returns:
        A list of string representations for each playbook.
    """
    async with SessionLocal() as db:
        playbook_filter = filters.PlaybookFilter(
            search=search,
        )
        if labels_id__in or labels_name__in or labels_category:
            playbook_filter.labels = filters.LabelFilter(
                id__in=labels_id__in,
                name__in=labels_name__in,
                category=labels_category,
            )
        playbooks = await crud.get_playbooks(db, playbook_filter, 0, 10000)
        if not playbooks:
            return ["No playbooks found matching the criteria."]
        return sequence_to_string_list(
            playbooks, schemas.ProxyChain
        )


@rg.tool
async def get_playbook_templates(
    search: Optional[str] = None,
    tactic: Optional[str] = None,
    technique: Optional[str] = None,
    labels_id__in: Optional[List[str]] = None,
    labels_name__in: Optional[List[str]] = None,
    labels_category: Optional[str] = None,
) -> List[str]:
    """
    Retrieves playbook templates and organizes them into a list and a map, with filtering options.
    Playbook templates are blueprints for creating new playbooks.
    Args:
        search: A general search string to apply across relevant template fields (name, yaml, tactic, technique).
                Use single argument query only, OR/AND/NOT is not supported.
        tactic: Filter templates by the MITRE ATT&CK Tactic they relate to (e.g., "Initial Access").
        technique: Filter templates by the MITRE ATT&CK Technique they relate to.
        labels_id__in: List of label IDs to include templates by.
        labels_name__in: List of label names to include templates by.
        labels_category: Category of labels to include templates by.
        labels_name__not_in: List of label names to exclude templates by.
    Returns:
        A dictionary containing:
        - 'templates': A list of string representations for each playbook template.
        - 'map': A dictionary mapping template IDs (string) to their full object dictionaries.
    """
    async with SessionLocal() as db:
        template_filter = filters.PlaybookTemplateFilter(
            search=search, tactic=tactic, technique=technique
        )
        if labels_id__in or labels_name__in or labels_category:
            template_filter.labels = filters.LabelFilter(
                id__in=labels_id__in,
                name__in=labels_name__in,
                category=labels_category,
            )
        playbook_templates = await crud.get_chain_templates(db, template_filter)
        if not playbook_templates:
            return ["No playbook templates found matching the criteria."]
        return sequence_to_string_list(playbook_templates, schemas.PlaybookTemplateView)


@rg.tool
async def get_proxies_info(
    search: Optional[str] = None,
    status: Optional[str] = None,
    labels_id__in: Optional[List[str]] = None,
    labels_name__in: Optional[List[str]] = None,
    labels_category: Optional[str] = None,
) -> List[str]:
    """
    Retrieves a list of all configured proxies, with various filtering options.
    Proxies facilitate network communication through compromised hosts.
    Args:
        order_by: Fields to order the results by (e.g., ["-time_created", "host"]).
        search: A general search string to apply across relevant proxy fields (host, type, status, note, remote_hostname).
                Use single argument query only, OR/AND/NOT is not supported.
        status: Filter by the current status of the proxy (e.g., "active", "inactive").
        labels_id__in: List of label IDs to include proxies by.
        labels_name__in: List of label names to include proxies by.
        labels_category: Category of labels to include proxies by.
    Returns:
        A list of string representations for each proxy.
    """
    async with SessionLocal() as db:
        proxy_filter = filters.ProxyFilter(
            search=search,
            status=status,
        )
        if labels_id__in or labels_name__in or labels_category:
            proxy_filter.labels = filters.LabelFilter(
                id__in=labels_id__in,
                name__in=labels_name__in,
                category=labels_category,
            )
        proxies = await crud.get_proxies(db, proxy_filter, limit=1000)
        return sequence_to_string_list(proxies, schemas.Proxy)


@rg.tool
async def get_previous_suggestions(
    c2_implant_id: Optional[str] = None,
    search: Optional[str] = None,
    playbook_template_id: Optional[str] = None,
    labels_id__in: Optional[List[str]] = None,
    labels_name__in: Optional[List[str]] = None,
    labels_category: Optional[str] = None,
) -> List[str]:
    """
    Retrieves previous suggestions, optionally filtered by various criteria.
    Suggestions provide historical recommendations or next steps generated by the system.
    Args:
        c2_implant_id: Filter suggestions by the ID of the C2 implant they relate to.
        search: A general search string to apply across relevant suggestion fields (name, reason).
                Use single argument query only, OR/AND/NOT is not supported.
        playbook_template_id: Filter by the ID of the playbook template that the suggestion might lead to.
        labels_id__in: List of label IDs to include suggestions by.
        labels_name__in: List of label names to include suggestions by.
        labels_category: Category of labels to include suggestions by.
    Returns:
        A list of string representations for each previous suggestion.
    """
    async with SessionLocal() as db:
        suggestion_filter = filters.SuggestionFilter(
            search=search,
            playbook_template_id=playbook_template_id,
            c2_implant_id=c2_implant_id,
        )
        if labels_id__in or labels_name__in or labels_category:
            suggestion_filter.labels = filters.LabelFilter(
                id__in=labels_id__in,
                name__in=labels_name__in,
                category=labels_category,
            )
        previous_suggestions = await crud.get_suggestions(
            db, suggestion_filter, limit=1000
        )
        return sequence_to_string_list(previous_suggestions, schemas.Suggestion)


@rg.tool
async def get_socks_servers_info(
    search: Optional[str] = None,
    status: Optional[str] = None,
    labels_id__in: Optional[List[str]] = None,
    labels_name__in: Optional[List[str]] = None,
    labels_category: Optional[str] = None,
) -> List[str]:
    """
    Retrieves a list of all configured SOCKS servers, with various filtering options.
    SOCKS servers enable proxying of network traffic through an established SOCKS proxy.
    Args:
        search: A general search string to apply across relevant SOCKS server fields (type, hostname, operating_system).
                Use single argument query only, OR/AND/NOT is not supported.
        status: Filter by the operational status of the SOCKS server (e.g., "connected").
        labels_id__in: List of label IDs to include SOCKS servers by.
        labels_name__in: List of label names to include SOCKS servers by.
        labels_category: Category of labels to include SOCKS servers by.
    Returns:
        A list of string representations for each SOCKS server.
    """
    async with SessionLocal() as db:
        socks_filter = filters.SocksServerFilter(
            search=search,
            status=status,
        )
        if labels_id__in or labels_name__in or labels_category:
            socks_filter.labels = filters.LabelFilter(
                id__in=labels_id__in,
                name__in=labels_name__in,
                category=labels_category,
            )
        socks_servers = await crud.get_socks_servers(db, socks_filter, limit=1000000)
        return sequence_to_string_list(socks_servers, schemas.SocksServer)


@rg.tool
async def get_credentials_info(
    search: Optional[str] = None,
    labels_id__in: Optional[List[str]] = None,
    labels_name__in: Optional[List[str]] = None,
    labels_category: Optional[str] = None,
    domain_search: Optional[str] = None,
) -> List[str]:
    """
    Retrieves a list of all stored credentials, with various filtering options.
    Credentials can include usernames, passwords, or Kerberos tickets.
    Args:
        search: A general search string to apply across relevant credential fields (username).
                Use single argument query only, OR/AND/NOT is not supported.
        username: Filter by a specific username.
        password_id: Filter by the ID of an associated password entry.
        kerberos_id: Filter by the ID of an associated Kerberos entry.
        labels_id__in: List of label IDs to include credentials by.
        labels_name__in: List of label names to include credentials by.
        domain_search: A general search string for the associated domain (short_name, long_name).
                       Use single argument query only, OR/AND/NOT is not supported.
    Returns:
        A list of string representations for each credential.
    """
    async with SessionLocal() as db:
        credential_filter = filters.CredentialFilter(
            search=search,
        )
        if labels_id__in or labels_name__in or labels_category:
            credential_filter.labels = filters.LabelFilter(
                id__in=labels_id__in,
                name__in=labels_name__in,
                category=labels_category,
            )
        if domain_search:
            credential_filter.domain = filters.DomainFilter(
                search=domain_search,
            )
        credentials = await crud.get_credentials(db, credential_filter, limit=100000)
        if not credentials:
            return ["No credentials found."]
        return sequence_to_string_list(credentials, schemas.Credential)


@rg.tool
async def get_situational_awareness_info(
    search: Optional[str] = None,
    name: Optional[str] = None,
    category: Optional[str] = None,
    domain_id: Optional[str] = None,
) -> List[str]:
    """
    Retrieves a list of all situational awareness entries, with various filtering options.
    Situational awareness provides context about the operational environment.
    Args:
        search: A general search string to apply across relevant SA fields (name, category, value_string).
                Use single argument query only, OR/AND/NOT is not supported.
        name: Filter by the name of the situational awareness entry.
        category: Filter by the category of the situational awareness entry (e.g., "Threat", "Vulnerability").
        domain_id: Filter by the ID of the domain associated with the situational awareness.
    Returns:
        A list of string representations for each situational awareness entry.
    """
    async with SessionLocal() as db:
        # sa_filter = filters.SituationalAwarenessFilter(
        #     search=search,
        #     name=name,
        #     category=category,
        #     domain_id=domain_id,
        # )
        situational_awareness = await crud.list_situational_awareness(
            db,
            name=name if name else "",
            category=category if category else "",
            domain_id=domain_id if domain_id else "",
        )
        return sequence_to_string_list(
            situational_awareness, schemas.SituationalAwareness
        )


@rg.tool
async def get_domains_info(
    search: Optional[str] = None,
    labels_id__in: Optional[List[str]] = None,
    labels_name__in: Optional[List[str]] = None,
    labels_category: Optional[str] = None,
) -> List[str]:
    """
    Retrieves a list of all known domains and organizes them into a list and a map, with filtering options.
    Domains represent network domains identified during operations.
    Args:
        search: A general search string to apply across relevant domain fields (short_name, long_name).
                Use single argument query only, OR/AND/NOT is not supported.
        labels_id__in: List of label IDs to include domains by.
        labels_name__in: List of label names to include domains by.
        labels_category: Category of labels to include domains by.
    Returns:
        - list of string representations for each domain.
    """
    async with SessionLocal() as db:
        domain_filter = filters.DomainFilter(
            search=search
        )
        if labels_id__in or labels_name__in or labels_category:
            domain_filter.labels = filters.LabelFilter(
                id__in=labels_id__in,
                name__in=labels_name__in,
                category=labels_category,
            )
        domains = await crud.get_domains(db, domain_filter, limit=100000)
        return sequence_to_string_list(domains, schemas.Domain)


@rg.tool
async def get_undownloaded_share_files(
    search: str = '',
    file_type: Optional[str] = "file", # Default to "file" as in your original filter
    limit: int = 1000, # Keep the large limit as in your original code
    labels_id__in: Optional[List[str]] = None,
    labels_name__in: Optional[List[str]] = None,
    labels_category: Optional[str] = None,
) -> List[str]:
    """
    Retrieves a list of shareable files that have not yet been downloaded.
    This tool is crucial for identifying potential files for download suggestions.
    Args:
        search: A general search string to apply across relevant file fields (e.g., name, path).
                Use single argument query only, OR/AND/NOT is not supported.
        file_type: Filter by the type of share file (e.g., "file", "directory"). Defaults to "file".
        limit: The maximum number of files to retrieve. Defaults to 1000.
        labels_id__in: List of label IDs to include share files by.
        labels_name__in: List of label names to include share files by.
        labels_category: Category of labels to include share files by.
    Returns:
        A list of string representations for each undownloaded share file.
    """
    async with SessionLocal() as db:
        share_file_filter = filters.ShareFileFilter(
            type=file_type,
            downloaded=False, # Explicitly filtering for undownloaded files
            search=search,
        )
        if labels_id__in or labels_name__in or labels_category:
            share_file_filter.labels = filters.LabelFilter(
                id__in=labels_id__in,
                name__in=labels_name__in,
                category=labels_category,
            )
        
        share_files = await crud.get_share_files(db, filters=share_file_filter, limit=limit)
        
        share_files_list = sequence_to_string_list(share_files, schemas.ShareFile)
        log.info(f"Retrieved {len(share_files_list)} undownloaded share files.")
        return share_files_list


@rg.tool
async def get_unindexed_share_folders(
    search: str = '',
    limit: int = 1000, # Providing a default limit for practicality
    labels_id__in: Optional[List[str]] = None,
    labels_name__in: Optional[List[str]] = None,
    labels_category: Optional[str] = None,
    indexed: bool = False, # Added a specific 'indexed' filter for flexibility
) -> List[str]:
    """
    Retrieves a list of share folders that are considered unindexed or have a specific index status.
    This tool is useful for identifying network shares that need further processing or analysis.
    Args:
        search: A general search string to apply across relevant share folder fields (e.g., name, path).
                Use single argument query only, OR/AND/NOT is not supported. Optional
        limit: The maximum number of share folders to retrieve, default 1000.
        labels_id__in: List of label IDs to include share folders by.
        labels_name__in: List of label names to include share folders by.
        labels_category: Category of labels to include share folders by.
        indexed: Boolean to filter by index status (True for indexed, False for unindexed, None for all).
    Returns:
        A list of string representations for each unindexed share folder.
    """
    async with SessionLocal() as db:
        # Assuming ShareFileFilter can filter by 'type' and potentially 'indexed' status
        share_folder_filter = filters.ShareFileFilter(
            type="dir", # Filter for directories to get folders
            search=search,
            indexed=indexed,
        )

        if labels_id__in or labels_name__in or labels_category:
            share_folder_filter.labels = filters.LabelFilter(
                id__in=labels_id__in,
                name__in=labels_name__in,
                category=labels_category,
            )
        
        # Assuming crud.get_share_files can handle filtering for directories and indexed status
        unindexed_folders = await crud.get_share_files(
            db,
            filters=share_folder_filter,
            limit=limit
        )
        
        result = sequence_to_string_list(unindexed_folders, schemas.ShareFile)
        log.info(f"Retrieved {len(result)} unindexed share folders.")
        return result


@rg.tool
async def get_hosts(
    search: str = "",
    neo4j_limit: int = 10000,
) -> List[str]:
    """
    Retrieves a list of active hosts, excluding those marked with a specific 'skip' label.
    This is useful for focusing on relevant hosts for further actions or analysis,
    bypassing hosts that are intentionally excluded (e.g., dead, test, or sensitive hosts).

    Args:
        search: An optional search string to filter hosts from the graph database (Neo4j).
        neo4j_limit: The maximum number of hosts to retrieve from the graph database.
    Returns:
        A list of string representations for each filtered host. If no hosts are found,
        returns a list containing the string "No hosts found.".
    """
    skip_label_id: str = "e6a57aae-993a-4196-a23a-13a7e5f607a3"
    async with SessionLocal() as db: # For SQL database access
        # 1. Get hosts from Neo4j
        async with get_async_neo4j_session_context() as graphsession:
            hosts_from_neo4j = await graph_crud.get_computers(graphsession, search, 0, neo4j_limit)
        log.info(f"Retrieved {len(hosts_from_neo4j)} hosts from Neo4j.")

        # 2. Get hosts to skip from SQL database
        skip_hosts_from_sql = await crud.get_hosts(
            db,
            filters=filters.HostFilter(
                labels=filters.LabelFilter(
                    id__in=[skip_label_id]
                )
            ),
            limit=10000, # Max limit for skip hosts
        )
        log.info(f"Retrieved {len(skip_hosts_from_sql)} hosts marked for skipping.")

        # 3. Build a set of uppercase host basenames to skip
        to_skip: set[str] = set()
        for skip_host in skip_hosts_from_sql:
            to_skip.add(f"{skip_host.name}".upper())
        log.info(f"Built skip list of size: {len(to_skip)}")

        # 4. Filter Neo4j hosts
        filtered_hosts_list = []
        for host in hosts_from_neo4j:
            host_name = host.get("name") if isinstance(host, dict) else getattr(host, "name", None)

            if not host_name:
                log.warning(f"Host found in Neo4j without a 'name' attribute: {host}")
                continue

            if "." in host_name:
                basename = host_name.split(".")[0]
                if basename.upper() in to_skip:
                    continue # Skip this host
            
            filtered_hosts_list.append(dict_to_string(host))
        
        log.info(f"Returning {len(filtered_hosts_list)} filtered hosts.")
        if not filtered_hosts_list:
            return ["No hosts found."]
        
        return filtered_hosts_list


@rg.tool
async def get_network_shares(
    search: str = '',
    limit: int = 1000, # Default to a large limit as in your original code
) -> List[str]:
    """
    Retrieves a list of network share UNC paths, excluding those marked with specific 'skip' labels.
    This tool is useful for identifying accessible shares that are not otherwise marked for exclusion
    (e.g., test shares, or shares already processed/irrelevant).

    Args:
        search: An optional search string to filter shares by name or path.
        limit: The maximum number of shares to retrieve. Defaults to 1000.
    Returns:
        A list of UNC paths (strings) for the filtered network shares.
    """
    skip_label_ids = ["3f061979-055d-473f-ba15-d7b508f0ba83", "851853d0-e540-4185-b46e-cf2e0cc63aa8"]
    async with SessionLocal() as db:
        share_filter = filters.ShareFilter(search=search)

        # Note: Your original code retrieves all shares and then filters in Python.
        # If your `crud.get_shares` or `ShareFilter` supports `not_labels` or `labels__not_in`,
        # it would be more efficient to apply the skip logic at the database level.
        # For now, I'm mirroring your existing Python-side filtering for direct replacement.
        all_shares = await crud.get_shares(db, share_filter, limit=limit)
        log.info(f"Retrieved {len(all_shares)} shares before applying skip filters.")

        to_skip_unc_paths: set[str] = set()
        for share in all_shares:
            # Assuming 'share.labels' is an iterable of label objects, each with an 'id' attribute
            if hasattr(share, 'labels') and share.labels: # Check if 'labels' attribute exists and is not empty
                for label in share.labels:
                    if str(label.id) in skip_label_ids:
                        # Assuming 'share.unc_path' is the attribute holding the UNC path
                        if hasattr(share, 'unc_path'):
                            to_skip_unc_paths.add(share.unc_path)
                        else:
                            log.warning(f"Share object missing 'unc_path' attribute: {share}")
                        break # No need to check other labels on this share once a skip label is found
        
        log.info(f"Identified {len(to_skip_unc_paths)} UNC paths to skip.")

        # Filter the shares based on the collected skip UNC paths
        filtered_shares_unc_paths = [
            share.unc_path
            for share in all_shares
            if hasattr(share, 'unc_path') and share.unc_path not in to_skip_unc_paths
        ]
        
        log.info(f"Returning {len(filtered_shares_unc_paths)} filtered network share UNC paths.")
        return filtered_shares_unc_paths


@rg.tool
async def list_filters(
    model_name: str,
) -> List[str]:
    """
    Retrieves a list of available filters for a given model.

    Args:
        model_name: The name of the model to retrieve filters for.
            Valid options are: "action", "c2_implant", "c2_job", "c2_output",
            "c2_server", "c2_task", "certificate_authority", "certificate_template",
            "checklist", "credential", "domain", "file", "highlight", "host",
            "issue", "objective", "playbook", "playbook_template", "proxy",
            "share", "share_file", "situational_awareness", "socks_job",
            "socks_server", "suggestion", "timeline".

    Returns:
        A list of string representations for each available filter.
    """
    async with SessionLocal() as db:
        filters_list = await crud.get_filters_for_model(
            db, model_name
        )
        return sequence_to_string_list(filters_list, schemas.Filter)


@rg.tool
async def create_suggestion_for_plan_step(plan_step_id: str, name: str, reason: str, playbook_template_id: str, arguments: str) -> str:
    """
    Creates a new suggestion linked to a specific plan step.
    IMPORTANT: The `plan_step_id` and `playbook_template_id` MUST be the IDs of existing objects.
    This tool validates that the IDs exist before creating the suggestion.
    Use the `get_plan_steps` and `get_playbook_templates` tools to find valid IDs.
    The arguments should be a json encoded dictionary.
    Output: A dictionary representation of the created suggestion, or an error string.
    """
    try:
        args_dict = json.loads(arguments)
    except json.JSONDecodeError:
        return "Error: The 'arguments' parameter must be a valid JSON-encoded dictionary string."

    async with SessionLocal() as db:
        # Validate plan_step_id
        plan_step = await crud.get_plan_step(db, plan_step_id)
        if not plan_step:
            return f"Error: Plan Step with ID '{plan_step_id}' not found. Please use a valid ID."

        # Validate playbook_template_id
        playbook_template = await crud.get_playbook_template(playbook_template_id)
        if not playbook_template:
            return f"Error: Playbook Template with ID '{playbook_template_id}' not found. Please use a valid ID from get_playbook_templates."

        # If validation passes, proceed to create the suggestion
        suggestion_schema = schemas.SuggestionCreate(
            plan_step_id=plan_step_id,
            name=name,
            reason=reason,
            playbook_template_id=playbook_template_id,
            arguments=args_dict
        )
        try:
            _, created_suggestion = await crud.create_suggestion(db, suggestion_schema)
            return f"Suggestion '{name}' created successfully with ID: {created_suggestion.id}"
        except Exception as e:
            log.error(f"Failed to create suggestion in database: {e}")
            return f"Error: An unexpected database error occurred while creating the suggestion."


@rg.tool
async def create_plan_step(plan_id: str, description: str, notes: str = "") -> str:
    """
    Creates a new step at the end of the specified plan. The order is determined automatically.
    Returns the ID of the newly created plan step.
    """
    async with SessionLocal() as db:
        # Automatically determine the next order number
        highest_order = await crud.get_highest_plan_step_order(db, plan_id)
        next_order = highest_order + 1

        _, new_step = await crud.create_plan_step(
            db,
            schemas.PlanStepCreate(
                plan_id=plan_id,
                description=description,
                order=next_order,
                notes=notes,
            ),
        )
        if not new_step:
            return "Error: Failed to create plan step."
        return str(new_step.id)


@rg.tool
async def update_plan_step(
    step_id: str,
    status: t.Literal["pending", "in_progress", "completed", "failed", "blocked", "skipped"],
    notes: Optional[str] = None,
) -> str | bool:
    """
    Updates the status and notes of an existing plan step.
    The 'status' parameter MUST be one of the following exact values: 'pending', 'in_progress', 'completed', 'failed', 'blocked', 'skipped'.
    Returns True on success, or an error string on failure.
    """
    # Layer 3: Runtime Validation
    valid_statuses = [s.value for s in PlanStepStatus]
    if status not in valid_statuses:
        return f"Error: Invalid status '{status}'. Please use one of the following: {', '.join(valid_statuses)}"

    async with SessionLocal() as db:
        update_data = schemas.PlanStepUpdate(status=status)
        if notes is not None:
            update_data.notes = notes
        
        updated_step = await crud.update_plan_step(
            db,
            id=step_id,
            plan_step=update_data,
        )
        return updated_step is not None


@rg.tool
async def delete_suggestion(suggestion_id: str) -> str:
    """
    Disassociates a suggestion from its plan step by setting its `plan_step_id` to null.
    This effectively removes the suggestion from the active plan for a cleaner view,
    without permanently deleting it from the database.
    """
    async with SessionLocal() as db:
        suggestion = await crud.get_suggestion(suggestion_id)
        if not suggestion:
            return f"Error: Suggestion with ID '{suggestion_id}' not found."
        await crud.delete_suggestion(db, suggestion_id)
    return f"Suggestion {suggestion_id} unlinked from plan successfully."


@rg.tool
async def update_suggestion(suggestion_id: str, name: Optional[str] = None, reason: Optional[str] = None, arguments: Optional[str] = None) -> str:
    """
    Updates the fields of an existing suggestion. All fields are optional.
    Use this to refine or correct a suggestion.
    """
    async with SessionLocal() as db:
        suggestion = await crud.get_suggestion(suggestion_id)
        if not suggestion:
            return f"Error: Suggestion with ID '{suggestion_id}' not found."

        update_data = schemas.SuggestionCreate()
        if name is not None:
            update_data.name = name
        if reason is not None:
            update_data.reason = reason
        if arguments is not None:
            try:
                update_data.arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return "Error: The 'arguments' parameter must be a valid JSON-encoded dictionary string."

        await crud.update_suggestion(db, suggestion_id, update_data)
        return f"Suggestion {suggestion_id} updated successfully."


@rg.tool
async def validate_playbook_arguments(playbook_template_id: str, arguments: str) -> str:
    """
    Performs a dry run validation for playbook arguments.
    It checks that the playbook_template_id exists and that any c2_implant_id included in the arguments corresponds to a real implant.
    This prevents errors when creating suggestions.
    """
    try:
        args_dict = json.loads(arguments)
    except json.JSONDecodeError:
        return "Error: The 'arguments' parameter must be a valid JSON-encoded dictionary string."

    playbook_template = await crud.get_playbook_template(playbook_template_id)
    if not playbook_template:
        return f"Error: Playbook Template with ID '{playbook_template_id}' not found."

    # This part is a simplified adaptation. A full implementation would parse the template's arg definitions.
    # For now, we focus on the most common and critical validation: c2_implant_id.
    if 'c2_implant_id' in args_dict:
        implant_id = args_dict['c2_implant_id']
        implant = await crud.get_c2_implant(implant_id)
        if not implant:
            return f"Error: C2 Implant with ID '{implant_id}' not found."

    return "Validation successful."
