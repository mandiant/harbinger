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
import rigging as rg
from harbinger.config import get_settings
from pydantic import field_validator
import typing as t

settings = get_settings()


attack_phases = [
    "initial reconnaissance",
    "initial compromise",
    "establish foothold",
    "escalate privileges",
    "internal reconnaissance",
    "move laterally",
    "maintain presence",
    "complete mission",
]

attack_phase_label_mapping = {
    "initial reconnaissance": "cf5d2e4a-0cbc-4f5e-85ef-da9d116df85e",
    "initial compromise": "65072ef0-7e98-404e-9ef0-001865a7c23a",
    "establish foothold": "f498828e-e563-45ea-b91f-bf2c1a844c95",
    "escalate privileges": "1492e045-d9eb-405b-8d74-f727327d36fb",
    "internal reconnaissance": "ee0dad20-8774-449a-a4b4-ceac1ce01455",
    "move laterally": "6780578e-a200-4127-a2c8-78ae4ba8d72b",
    "maintain presence": "e542fe7d-1cff-4026-9b08-7a15a13db3ca",
    "complete mission": "fa3ffd5e-fa59-439e-bf06-26d10a045fec",
}

attack_phase_mapping = {
    "information gathering": "initial reconnaissance",
    "scanning": "initial reconnaissance",
    "footprinting": "initial reconnaissance",
    "profiling": "initial reconnaissance",
    "osint collection": "initial reconnaissance",
    "exploitation": "initial compromise",
    "breach": "initial compromise",
    "intrusion": "initial compromise",
    "gaining access": "initial compromise",
    "zero-day attack": "initial compromise",
    "persistence": "establish foothold",
    "anchoring": "establish foothold",
    "backdooring": "establish foothold",
    "command and control (c2) setup": "establish foothold",
    "privilege escalation": "escalate privileges",
    "gaining elevated access": "escalate privileges",
    "root compromise": "escalate privileges",
    "discovery": "internal reconnaissance",
    "enumeration": "internal reconnaissance",
    "network mapping": "internal reconnaissance",
    "system analysis": "internal reconnaissance",
    "lateral movement": "move laterally",
    "pivoting": "move laterally",
    "island hopping": "move laterally",
    "spreading": "move laterally",
    "command and control (c2)": "maintain presence",
    "remote access": "maintain presence",
    "staying hidden": "maintain presence",
    "exfiltration": "complete mission",
    "impact": "complete mission",
    "data theft": "complete mission",
    "disruption": "complete mission",
    "denial of service": "complete mission",
    "destruction": "complete mission",
}


safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

generator = rg.get_generator(
    settings.gemini_model,
    params=rg.GenerateParams(extra=dict(safety_settings=safety_settings)),
)


class Credential(rg.Model):
    password: str = rg.element(default="")
    username: str = rg.element(default="")
    domain: str = rg.element(default="")


class ListOfCredentials(rg.Model):
    found_credentials: bool = rg.element()
    credentials: list[Credential] = rg.wrapped("credentials", rg.element(default=[]))

    @classmethod
    def xml_example(cls) -> str:
        return ListOfCredentials(
            found_credentials=True,
            credentials=[
                Credential(
                    password="password",
                    username="username",
                    domain="test.local",
                )
            ],
        ).to_pretty_xml()


class Summary(rg.Model):
    text: t.Annotated[
        str, rg.Ctx(example="Used wmiexec.py to execute cmd.exe on HOSTNAME.LOCAL")
    ] = rg.element()
    error: t.Annotated[bool, rg.Ctx(example="False")] = rg.element()
    successful: t.Annotated[bool, rg.Ctx(example="True")] = rg.element()
    status: t.Annotated[str, rg.Ctx(example="completed/error")] = rg.element()
    attack_lifecycle: t.Annotated[str, rg.Ctx(example=",".join(attack_phases))] = (
        rg.element()
    )

    @classmethod
    def xml_example(cls) -> str:
        return Summary(
            text="Used wmiexec.py to execute cmd.exe on HOSTNAME.LOCAL",
            error=False,
            successful=True,
            status="completed",
            attack_lifecycle=attack_phases[5],
        ).to_pretty_xml()

    @field_validator("error", mode="before")
    def parse_str_to_bool(cls, v: t.Any) -> t.Any:
        if isinstance(v, str):
            if v.strip().lower().startswith("yes"):
                return True
            elif v.strip().lower().startswith("no"):
                return False
        return v

    @field_validator("attack_lifecycle", mode="before")
    def parse_attack_lifecycle(cls, v: t.Any) -> t.Any:
        value = v.strip().lower()
        if value in attack_phases:
            return value
        elif value in attack_phase_mapping:
            return attack_phase_mapping[value]
        raise ValueError(
            f"not a valid attack phase, pick from: {','.join(attack_phases)}"
        )


@generator.prompt
async def find_credentials(text: str) -> ListOfCredentials:
    """Analyze the provided file and extract all verifiable credentials with high precision, minimizing false positives. Focus exclusively on identifying legitimate username/password pairs, and strictly avoid reporting data that only superficially resembles a credential.  Leverage contextual clues such as proximity to labels like "username," "password," "login," "credentials," "account," etc., and analyze surrounding data structures (e.g., key-value pairs, forms, tables) to validate potential credentials and disambiguate from similar-looking data.  Consider different credential formats, including email addresses, usernames with special characters, and potentially obfuscated credentials, but only report credentials that are explicitly present in the file. Do not fabricate, guess, or infer credentials.  For each extracted credential, adhere to this precise output structure:

* **Clearly specify the `username` and `password`.**

* **If a username includes an "@" symbol:**
    * Parse it into two separate fields:  `"username"` (the part before the "@") and `"domain"` (the part after the "@").  For Example:  `{"username": "john.doe", "domain": "example.com", "password": "password123"}`

* **If the username does *not* contain an "@" symbol:**
    * Provide the entire username as a single `"username"` field. For Example: `{"username": "johndoe", "password": "password123"}`

Do not deviate from the specified output structure. Do not include any additional information or commentary."""


@generator.prompt
async def summarize_action(command: str, arguments: str, output: str) -> Summary:
    """Hi, You are a cyber security expert, can you please write a short summary of this action and output that was performed?
    Write in active voice and use "the Red Team" as the person instantiating the action, do not use attempted to and was able to.
    Do not include passwords in the output summary.
    Do not provide output about any guid identifiers and do not say anything about "safe".
    """


@generator.prompt
async def summarize_attack_path(summaries: list[str]) -> str:
    """Hi, You are a cyber security expert, can you please write an attack path of these summaries of actions?
    Write in active voice and do not use attempted to and was able to. Please write it as an interesting story.
    Please ignore actions that failed and only write about the importatnt steps in the attack path that brought the red team closer to their goal.
    """


class Playbook(rg.Model):
    playbook_id: t.Annotated[
        str, rg.Ctx(example="131cc3c9-e5da-4b3a-8db6-0ea47e7fc4f8")
    ] = rg.element()
    arguments: t.Annotated[t.Optional[str], rg.Ctx(example="")] = rg.element(default="")

    @field_validator("arguments", mode="before")
    def check_arguments(cls, v: t.Any) -> t.Any:
        if v:
            json.loads(v)
        return v


class Command(rg.Model):
    command_name: t.Annotated[t.Optional[str], rg.Ctx(example="ps")] = rg.element(
        default=""
    )
    arguments: t.Annotated[t.Optional[str], rg.Ctx(example="")] = rg.element(default="")


class Action(rg.Model):
    playbook: Playbook = rg.element()
    # command: Command | None = rg.element(default=None)
    reason: t.Annotated[
        str,
        rg.Ctx(
            example="This command has not been executed yet and is the next according to the documentation"
        ),
    ] = rg.element()
    name: t.Annotated[str, rg.Ctx(example="Run ps")] = rg.element()

    @classmethod
    def xml_example(cls) -> str:
        return Action(
            playbook=Playbook(
                playbook_id="131cc3c9-e5da-4b3a-8db6-0ea47e7fc4f8",
                arguments='{"some_id":"123", "vulnerable": false}',
            ),
            reason="Next logical action.",
            # command=None,
            name="Run ps",
        ).to_pretty_xml()


class ActionList(rg.Model):
    actions: list[Action] | None = rg.element(default=None)

    @classmethod
    def xml_example(cls) -> str:
        return ActionList(
            actions=[
                Action(
                    playbook=Playbook(
                        playbook_id="131cc3c9-e5da-4b3a-8db6-0ea47e7fc4f8",
                        arguments='{"some_id":"123", "vulnerable": false}',
                    ),
                    reason="Next logical action.",
                    # command=None,
                    name="Run ps",
                )
            ]
        ).to_pretty_xml()


@generator.prompt
async def suggest_action_c2_implant(
    additional_prompt: str,
    tasks_executed: list[str],
    implant_information: str,
    executed_playbooks_list: list[str],
    playbook_template_list: list[str],
    previous_suggestions: list[str],
    proxies: list[str],
    socks_servers: list[str],
) -> ActionList:
    """Hi, You are a cyber security expert, you will get a list of tasks that have been executed so far and some information on an implant that is running on a system.
    There is also a list of playbooks of which you can select an action.
    Can you please indicate what command should be executed next on this implant with the following requirements:

    * If commands are successful you don't need to run them again.
    * If there is already a suggestion for a particular action you don't need to give it again, unless the associated playbook did not succeed.
    * The labels object will indicate which software and edrs were found.
    * Make sure you are using stealthy techniques and try to blend into the environment
    * Determine if an attack is likely to be detected by an EDR
    * SentinelOne will detect runassembly based tasks, but won't detect any socks based tasks
    * CrowdStrike will detect runassembly or socks based tasks.
    * Windows defender will not detect any tasks.

    Generally speaking you should do the following per host:
    * run initial recon
    * Check the host for interesting information

    You should do the following per implant:
    * disable defences

    Please encode the optional arguments for each playbook as json blob.
    Give an empty action list like <action-list></action-list> if there are no new actions to perform.
    """


@generator.prompt
async def suggest_domain_action(
    additional_prompt: str,
    edr_detections: str,
    domain_checklist: str,
    checklist: list[str],
    tasks_executed: list[str],
    implants_information: list[str],
    executed_playbooks_list: list[str],
    playbook_template_list: list[str],
    previous_suggestions: list[str],
    proxies: list[str],
    socks_servers: list[str],
    credentials: list[str],
    situational_awareness: list[str],
) -> ActionList:
    """Hi, You are a cyber security expert, you will get a list of tasks that have been executed so far and some information on an implant that is running on a system.
    There is also a list of playbooks of which you can select an action.

    Can you please indicate what command should be executed next on one (or more implants) with the following requirements:

    * If commands are successful you don't need to run them again.
    * If there is already a suggestion for a particular action you don't need to give it again.
    * The labels object will indicate which software and edrs were found.
    * Make sure you are using stealthy techniques and try to blend into the environment
    * Determine if an attack is likely to be detected by an EDR
    * Only suggest actions for implants that have recently checked in (and don't have a Dead label).
    * Return 0 actions in case you don't think there is more to be done.

    The following data will indicate which actions are detected per EDR:

    {{ edr_detections }}

    You should do the following per domain:

    {{ domain_checklist }}

    This is the checklist you've made so far with all the steps and status of the progress of the checklist above:

    {{ checklist }}

    Please try to fill in all fields for each playbook and use the situational awareness output to get values for values like domain controller and dns server.

    Please encode the optional arguments for each playbook as json blob.
    Give an empty action list like <action-list></action-list> if there are no new actions to perform.
    """


class CheckListAction(rg.Model):
    name: str = rg.element()
    status: str = rg.element()
    reason: str = rg.element()


class Phase(rg.Model):
    name: str = rg.element(attr="name")
    status: str = rg.element(attr="status")
    reason: str = rg.element(attr="reason")
    actions: list[CheckListAction] = rg.element(name="action")


class Implant(rg.Model):
    implant_id: str = rg.element(attr="id")
    checklist: list[Phase] = rg.element(name="checklist")


class Domain(rg.Model):
    name: str = rg.element(attr="name")
    checklist: list[Phase] = rg.element(name="checklist")


class CheckList(rg.Model):
    domain_checklist: list[Domain] = rg.element(name="domain_checklist")

    @classmethod
    def xml_example(cls) -> str:
        return CheckList(
            domain_checklist=[
                Domain(
                    name="test.local",
                    checklist=[
                        Phase(
                            name="Domain reconnaissance",
                            status="completed",
                            reason="All domain reconnaissance tasks are completed.",
                            actions=[
                                CheckListAction(
                                    name="Enumerate domain password policy",
                                    status="completed",
                                    reason="We enumerated the domain password policy"
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ).to_pretty_xml()


@generator.prompt
async def create_checklist(
    domains: list[str],
    objectives: list[str],
    additional_prompt: str,
    checklist: str,
    previous_checklist: list[str],
    tasks_executed: list[str],
    implants_information: list[str],
    executed_playbooks_list: list[str],
    proxies: list[str],
    socks_servers: list[str],
    credentials: list[str],
    situational_awareness: list[str],
) -> CheckList:
    """Hi, You are a cyber security expert, you will get a list of tasks that have been executed so far and some information on a implants that are running on systems.
    There will be the following: tasks_executed and its output, implants information, executed playbooks, proxies, socks servers, credentials and situational awareness.
    The objectives that should be achieved and a checklist of actions that should be performed. You will also get the previous checklist that you've made (if its available).
    Can you make or update the checklist for the domains to show which phases in the checklist were completed and what actions are outstanding.
    Please add additional items on the Checklist to achieve the objectives.
    Only include actions for a domain and not about implant or host specific things.
    Only include entries for each domain in the domains list.
    In the mindmap there may be multiple tools that have the same effect or outcome and only one of them needs to be executed for success.

    Keep the next objectives in mind:

    {{ objectives }}

    Thanks!
    """


class File(rg.Model):

    unc_path: str = rg.element()
    reason: str = rg.element(alias="reason")


class Files(rg.Model):
    files: list[File] | None = rg.element(default=None)
    c2_implant_id: str | None = rg.element(default=None)

    @classmethod
    def xml_example(cls) -> str:
        return Files(
            files=[
                File(
                    unc_path="\\\\castelblack.north.sevenkingdoms.local\\C$\\Program Files (x86)\\Microsoft SQL Server Management Studio 20\\Common7\\IDE\\SqlWorkbenchProjectItems\\Sql\\Service Broker\\Security\\Create Private Key Certificate.sql",
                    reason="SQL file, potentially containing sensitive information or logic related to database security.",
                ),
                File(
                    unc_path="\\\\castelblack.north.sevenkingdoms.local\\C$\\Program Files (x86)\\Microsoft SQL Server Management Studio 20\\Common7\\IDE\\SqlWorkbenchProjectItems\\Sql\\Earlier Versions\\Manage Logins, Roles, and Users\\Add SQL Server Login.sql",
                    reason="SQL file, potentially containing logic for adding SQL Server logins, which could be a point of vulnerability.",
                ),
            ],
            c2_implant_id="e7d73d39-88b0-4900-b1a1-49205b56fde9",
        ).to_pretty_xml()


class Directories(rg.Model):
    files: list[File] | None = rg.element(default=None)
    c2_implant_id: str | None = rg.element(default=None)

    @classmethod
    def xml_example(cls) -> str:
        return Directories(
            files=[
                File(
                    unc_path="\\\\castelblack.north.sevenkingdoms.local\\C$\\Secrets\\",
                    reason="Could contain useful files.",
                ),
            ],
            c2_implant_id="e7d73d39-88b0-4900-b1a1-49205b56fde9",
        ).to_pretty_xml()


class Host(rg.Model):
    hostname: str = rg.element()
    reason: str = rg.element(alias="reason")


class Hosts(rg.Model):
    host_list: list[Host] = rg.element()
    c2_implant_id: str = rg.element()

    @classmethod
    def xml_example(cls) -> str:
        return Hosts(
            host_list=[Host(hostname="host1.domain.local", reason="File server")],
            c2_implant_id="e7d73d39-88b0-4900-b1a1-49205b56fde9",
        ).to_pretty_xml()


class Share(rg.Model):
    share_name: str = rg.element()
    reason: str = rg.element(alias="reason")


class Shares(rg.Model):
    share_list: list[Share] | None = rg.element(default=None)
    c2_implant_id: str | None = rg.element(default=None)

    @classmethod
    def xml_example(cls) -> str:
        return Shares(
            share_list=[Share(share_name="\\\\host1.domain.local\\NETLOGON", reason="Netlogon share could contain files with credentials")],
            c2_implant_id="e7d73d39-88b0-4900-b1a1-49205b56fde9",
        ).to_pretty_xml()


@generator.prompt
async def suggest_file_download_actions(
    share_files: list[str],
    implants_information: list[str],
    interesting_files: str,
) -> Files:
    """Hi, You are a cyber security expert, you will get a list of files that have been gathered and a list of interesting files according to our documentation. We are looking for files that contain credentials.
    Can you please provide us with a list of files that we should investigate further and select a suitable implant to download these files.

    {{ interesting_files }}

    In case there are no valid directories to list give us an empty list of files like this: <files></files>.
    Only refer to files in the share_file list, do not make up any new names. Be extra strict on downloading files from System32.
    """


@generator.prompt
async def suggest_dir_list_actions(
    share_files: list[str],
    implants_information: list[str],
) -> Directories:
    """Hi, You are a cyber security expert, you will get a list of directories that have been gathered.
    Can you please provide us with a list of directories that we should investigate further and select a suitable implant to list these directories.
    In case there are no valid directories to list give us an empty list of directories like this: <directories></directories>.
    Only refer to files in the share_file list, do not make up any new names. Be extra strict on listing files in System32
    """


@generator.prompt
async def suggest_hosts_list_shares(
    hosts: list[str],
    implants_information: list[str],
) -> Hosts:
    """Hi, You are a cyber security expert, you will get a list of hosts that have been gathered.
    Can you please provide us with a list of hosts that may contain interesting files and select a suitable implant to list these shares.
    """


@generator.prompt
async def suggest_shares_list(
    shares: list[str],
    implants_information: list[str],
) -> Shares:
    """Hi, You are a cyber security expert, you will get a list of shares that have been gathered but we did not yet list the root.
    Can you please provide us with a list of shares from <shares> input that may contain interesting files and select a suitable implant to list the root these shares.
    Do not make up new shares. If there are not results yield an empty <shares></shares> result.
    """


class DetectionRisk(rg.Model):
    value: int = rg.element()
    reason: str = rg.element(alias="reason")

    @classmethod
    def xml_example(cls) -> str:
        return DetectionRisk(
            value=1,
            reason="None of the EDRs in the labels are known to detect this action."
        ).to_pretty_xml()
    
    @field_validator("value", mode="before")
    def parse_value(cls, v: t.Any) -> t.Any:
        value = int(v)
        if value > 0 and value < 6:
            return v
        raise ValueError("value should be between 1 and 5")


@generator.prompt
async def c2_job_detection_risk(
    additional_prompt: str,
    action: str,
    detection_risk: str,
    c2_implant_information: str,
) -> DetectionRisk:
    """Hi, You are a cyber security expert, you will get an action that we would like to perform, please determine how likely it is to be detected.
    Use the following information:
    * The detection_risk string will contain information about certain EDRs and what actions they detect.
    * c2_implant_information contains information about the c2 implant that is used for this action.
    * Use the tags of the c2_implant to see which EDRs (and other software) is installed on the host where the implant runs.
    * Absence of a a label indicates that the EDR is not installed on that system.
    * Give a value of 1 (no detection risk) to 5 (Will get detected) in your output.
    * Please provide a reason so we can follow your thought process.


    {{ additional_prompt }}
    """
