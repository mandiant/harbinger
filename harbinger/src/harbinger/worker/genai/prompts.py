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
import re
import typing as t
import uuid

import rigging as rg
import yaml
from harbinger import schemas
from harbinger.config import get_settings
from harbinger.worker.genai import prompt_vars
from pydantic import (
    ValidationError as PydanticValidationError,
)
from pydantic import field_validator

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
    params=rg.GenerateParams(extra={"safety_settings": safety_settings}),
)


class Credential(rg.Model):
    password: str = rg.element()
    username: str = rg.element()
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
                ),
            ],
        ).to_pretty_xml()


class Summary(rg.Model):
    text: t.Annotated[
        str,
        rg.Ctx(example="Used wmiexec.py to execute cmd.exe on HOSTNAME.LOCAL"),
    ] = rg.element()
    error: t.Annotated[bool, rg.Ctx(example="False")] = rg.element()
    successful: t.Annotated[bool, rg.Ctx(example="True")] = rg.element()
    status: t.Annotated[str, rg.Ctx(example="completed/error")] = rg.element()
    attack_lifecycle: t.Annotated[str, rg.Ctx(example=",".join(attack_phases))] = rg.element()

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
    @classmethod
    def parse_str_to_bool(cls, v: t.Any) -> t.Any:
        if isinstance(v, str):
            if v.strip().lower().startswith("yes"):
                return True
            if v.strip().lower().startswith("no"):
                return False
        return v

    @field_validator("attack_lifecycle", mode="before")
    @classmethod
    def parse_attack_lifecycle(cls, v: t.Any) -> t.Any:
        value = v.strip().lower()
        if value in attack_phases:
            return value
        if value in attack_phase_mapping:
            return attack_phase_mapping[value]
        msg = f"not a valid attack phase, pick from: {','.join(attack_phases)}"
        raise ValueError(
            msg,
        )


@generator.prompt
async def find_credentials(text: str) -> ListOfCredentials:  # type: ignore
    """Analyze the provided file and extract all verifiable credentials with high precision, minimizing false positives. Focus exclusively on identifying legitimate username/password pairs, and strictly avoid reporting data that only superficially resembles a credential.  Leverage contextual clues such as proximity to labels like "username," "password," "login," "credentials," "account," etc., and analyze surrounding data structures (e.g., key-value pairs, forms, tables) to validate potential credentials and disambiguate from similar-looking data.  Consider different credential formats, including email addresses, usernames with special characters, and potentially obfuscated credentials, but only report credentials that are explicitly present in the file. Do not fabricate, guess, or infer credentials.  For each extracted credential, adhere to this precise output structure:

    * **Clearly specify the `username` and `password`.**

    * **If a username includes an "@" symbol:**
        * Parse it into two separate fields:  `"username"` (the part before the "@") and `"domain"` (the part after the "@").  For Example:  `{"username": "john.doe", "domain": "example.com", "password": "password123"}`

    * **If the username does *not* contain an "@" symbol:**
        * Provide the entire username as a single `"username"` field. For Example: `{"username": "johndoe", "password": "password123"}`

    Do not deviate from the specified output structure. Do not include any additional information or commentary.
    """


@generator.prompt
async def summarize_action(command: str, arguments: str, output: str) -> Summary:  # type: ignore
    """Hi, You are a cyber security expert, can you please write a short summary of this action and output that was performed?
    Write in active voice and use "the Red Team" as the person instantiating the action, do not use attempted to and was able to.
    Do not include passwords in the output summary.
    Do not provide output about any guid identifiers and do not say anything about "safe".
    """


@generator.prompt
async def summarize_attack_path(summaries: list[str]) -> str:  # type: ignore
    """Hi, You are a cyber security expert, can you please write an attack path of these summaries of actions?
    Write in active voice and do not use attempted to and was able to. Please write it as an interesting story.
    Please ignore actions that failed and only write about the importatnt steps in the attack path that brought the red team closer to their goal.
    """


class Playbook(rg.Model):
    playbook_id: t.Annotated[
        str,
        rg.Ctx(example="131cc3c9-e5da-4b3a-8db6-0ea47e7fc4f8"),
    ] = rg.element()
    arguments: t.Annotated[str | None, rg.Ctx(example="")] = rg.element(default="")

    @field_validator("arguments", mode="before")
    @classmethod
    def check_arguments(cls, v: t.Any) -> t.Any:
        if v:
            json.loads(v)
        return v


class Command(rg.Model):
    command_name: t.Annotated[str | None, rg.Ctx(example="ps")] = rg.element(
        default="",
    )
    arguments: t.Annotated[str | None, rg.Ctx(example="")] = rg.element(default="")


class Action(rg.Model):
    playbook: Playbook = rg.element()
    # command: Command | None = rg.element(default=None)
    reason: t.Annotated[
        str,
        rg.Ctx(
            example="This command has not been executed yet and is the next according to the documentation",
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
                ),
            ],
        ).to_pretty_xml()


@generator.prompt
async def suggest_action_c2_implant(
    additional_prompt: str,
    implant_information: str,
) -> ActionList:  # type: ignore
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
) -> ActionList:  # type: ignore
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

    Please try to fill in all fields for each playbook and use the situational awareness output to get values for values like domain controller and dns server.

    Please encode the optional arguments for each playbook as json blob.
    Give an empty action list like <action-list></action-list> if there are no new actions to perform.
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
    host_list: list[Host] = rg.element(default=[])
    c2_implant_id: str = rg.element(default="")

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
            share_list=[
                Share(
                    share_name="\\\\host1.domain.local\\NETLOGON",
                    reason="Netlogon share could contain files with credentials",
                ),
            ],
            c2_implant_id="e7d73d39-88b0-4900-b1a1-49205b56fde9",
        ).to_pretty_xml()


@generator.prompt
async def suggest_file_download_actions(
    interesting_files: str,
) -> Files:  # type: ignore
    """Hi, You are a cyber security expert, you will get a list of files that have been gathered and a list of interesting files according to our documentation. We are looking for files that contain credentials.
    Can you please provide us with a list of files that we should investigate further and select a suitable implant to download these files.

    {{ interesting_files }}

    In case there are no valid directories to list give us an empty list of files like this: <files></files>.
    Only refer to files in the share_file list, do not make up any new names. Be extra strict on downloading files from System32.
    """


@generator.prompt
async def suggest_dir_list_actions() -> Directories:  # type: ignore
    """Hi, You are a cyber security expert, you will get a list of directories that have been gathered.
    Can you please provide us with a list of directories that we should investigate further and select a suitable implant to list these directories.
    In case there are no valid directories to list give us an empty list of directories like this: <directories></directories>.
    Only refer to files in the share_file list, do not make up any new names. Be extra strict on listing files in System32
    """


@generator.prompt
async def suggest_hosts_list_shares() -> Hosts:  # type: ignore
    """Hi, You are a cyber security expert, you will get a list of hosts that have been gathered.
    Can you please provide us with a list of hosts that may contain interesting files and select a suitable implant to list these shares.
    """


@generator.prompt
async def suggest_shares_list() -> Shares:  # type: ignore
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
            reason="None of the EDRs in the labels are known to detect this action.",
        ).to_pretty_xml()

    @field_validator("value", mode="before")
    @classmethod
    def parse_value(cls, v: t.Any) -> t.Any:
        value = int(v)
        if value > 0 and value < 6:
            return v
        msg = "value should be between 1 and 5"
        raise ValueError(msg)


def replace_id(yaml_string: str) -> str:
    try:
        new_id = str(uuid.uuid4())
        # Match the whole line starting with 'id:'
        pattern = r"^id:\s*.*$"  # Added $ to match end of line explicitly
        # Replace with a simple f-string
        replacement = f"id: {new_id}"
        if not isinstance(yaml_string, str):
            print(f"Error: Input was not a string, but {type(yaml_string)}")
            return yaml_string

        updated_yaml_string_re, replacements_made = re.subn(
            pattern,
            replacement,
            yaml_string,
            count=1,
            flags=re.MULTILINE,
        )
        if replacements_made == 0:
            print("Warning: Line starting with 'id:' not found. Original string kept.")
            return yaml_string
        return updated_yaml_string_re
    except Exception as e:
        print(f"Error during regex substitution: {e}")
    return yaml_string


@generator.prompt
async def c2_job_detection_risk(
    additional_prompt: str,
    action: str,
    detection_risk: str,
    c2_implant_information: str,
) -> DetectionRisk:  # type: ignore
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


@generator.prompt
async def kerberoasting(
    additional_prompt: str,
    kerberoastable_users: list[str],
) -> ActionList:  # type: ignore
    """Hi, You are a cyber security expert, you will get a list of users that are kerberoastable, can you please select the best users to target. Be specific and make sure you only kerberoast everyone if all targets are a good target or no data is available.

    Use the following information:
    * Users in high privileged groups are valuable.
    * Use the number or privileges as more privileges is better
    * Check the last logon and password changed values.

    {{ additional_prompt }}
    """


# # --- Pydantic schema for basic YAML structure validation ---
# # Define this according to the essential fields your playbook requires.
# class BasicPlaybookStructure(BaseModel):
#     id: uuid.UUID | str # Allow string initially if AI might not generate perfect UUID
#     name: str
#     icon: t.Optional[str] = None
#     step_delay: t.Optional[int] = None
#     args: t.Optional[list] = None
#     steps: str # Check if 'steps' key exists and is a string (multiline YAML)

#     # Add other mandatory fields as needed for basic validation


# --- Output Model for Rigging ---
# This model defines the expected output structure for the rigging generator.
# In this case, it's just a single field containing the generated YAML.
class PlaybookYamlOutput(rg.Model):
    # Define the single field using Annotated and rg.Ctx like the example
    yaml_content: str = rg.element()

    # Add validation directly within the rigging model using a validator.
    # This validator runs *after* the LLM generates the content for yaml_content.
    @field_validator("yaml_content", mode="before")
    @classmethod
    def validate_yaml_content(cls, v: t.Any) -> str:
        """Validates the generated string ('v') to ensure it is valid YAML
        and conforms to the BasicPlaybookStructure.
        Raises ValueError on failure, which rigging typically handles.
        """
        if not isinstance(v, str):
            # Should already be a string based on type hint, but safety check
            msg = f"Expected string output for yaml_content, but got {type(v)}"
            raise ValueError(
                msg,
            )

        generated_yaml = v.strip()
        if not generated_yaml:
            msg = "Generated YAML content cannot be empty."
            raise ValueError(msg)

        generated_yaml = generated_yaml.replace("```yaml", "")
        generated_yaml = generated_yaml.replace("```", "")

        try:
            # 1. Validate YAML syntax
            parsed_yaml = yaml.safe_load(generated_yaml)
            if not isinstance(parsed_yaml, dict):
                msg = "Generated output is not a valid YAML dictionary/mapping."
                raise ValueError(
                    msg,
                )
            schemas.PlaybookTemplateGenerated(**parsed_yaml)
            return replace_id(generated_yaml)

        except (yaml.YAMLError, PydanticValidationError, ValueError) as e:
            # If any validation step fails, raise a ValueError.
            # Rigging's error handling mechanism should catch this.
            # Include details for debugging.
            error_message = f"Generated YAML failed validation: {e}. Content received:\n---\n{generated_yaml}\n---"
            print(
                f"Validation Error: {error_message}",
            )  # Optional: log the error server-side
            raise ValueError(
                error_message,
            )  # Raise ValueError to signal validation failure
        except Exception as e:
            # Catch any other unexpected validation errors
            error_message = (
                f"Unexpected validation error ({type(e).__name__}): {e}. Content received:\n---\n{generated_yaml}\n---"
            )
            print(f"Validation Error: {error_message}")
            raise ValueError(error_message)


@generator.prompt  # Use your specific configured generator instance
async def generate_playbook_yaml(
    readme_content: str,
    playbook_format_description: str = prompt_vars.PLAYBOOK_FORMAT_DESCRIPTION,
    yaml_examples: str = prompt_vars.PLAYBOOK_EXAMPLES,
) -> PlaybookYamlOutput:  # type: ignore
    """You are an expert system specializing in cybersecurity automation and creating structured playbook templates in YAML format.
    Your goal is to generate a valid playbook YAML based *only* on the provided README documentation, adhering strictly to the specified format and drawing inspiration from the examples.

    Where possible try to use the Credential object in your playbooks by setting a credential_id and using the fields as shown below:

    class Credential(BaseModel):
        domain: Domain | None = None
        password: Password | None = None
        kerberos: Kerberos | None = None
        labels: List["Label"] | None = None

    class Password(BaseModel):
        password: str | None = None
        nt: str | None = None
        aes256_key: str | None = None
        aes128_key: str | None = None

    class Domain(BaseModel):
        short_name: str | None = None
        long_name: str | None = None

    If you use a credential object don't include the credential related fields.

    If more steps are required you can include multiple steps in the output.
    """


class PlanStepOutput(rg.Model):
    """Represents a single step in a newly generated plan."""

    description: str = rg.element()
    order: int = rg.element()
    notes: str = rg.element(default="")

    @classmethod
    def xml_example(cls) -> str:
        return cls(
            description="Perform initial reconnaissance on the target domain.",
            order=1,
            notes="Use open-source intelligence (OSINT) tools to gather information.",
        ).to_pretty_xml()


class GeneratedPlan(rg.Model):
    """The complete output for a new plan generation request."""

    steps: list[PlanStepOutput] = rg.element(default=[])

    @classmethod
    def xml_example(cls) -> str:
        return cls(
            steps=[
                PlanStepOutput(
                    description="Enumerate public-facing web servers.",
                    order=1,
                    notes="Focus on identifying technologies and potential vulnerabilities.",
                ),
                PlanStepOutput(
                    description="Scan for open ports on discovered servers.",
                    order=2,
                ),
            ],
        ).to_pretty_xml()


@generator.prompt
async def generate_testing_plan(objectives: str, current_state: str) -> GeneratedPlan:  # type: ignore
    """You are an expert penetration testing planner. Your role is to create a high-level, strategic plan to achieve a specific security assessment objective.

    **Your Goal:**
    Based on the provided `objectives` and a `current_state` summary of the environment, generate a structured, logical, and actionable testing plan.

    **Input:**
    1.  `objectives`: A string describing the high-level goal of the penetration test (e.g., "Become domain admin in NORTH", "Exfiltrate customer database").
    2.  `current_state`: A summary of the database, indicating what is already known about the environment (e.g., number of hosts, credentials, active implants).

    **Your Task:**
    1.  **Analyze Inputs:** Carefully consider the main `objective` in the context of the `current_state`.
    2.  **Formulate a Strategy:** Devise a high-level, step-by-step strategy to get from the `current_state` to achieving the `objective`.
    3.  **Use Tools (Optional):** While the primary input is the summary, you can use your tools (e.g., `get_playbook_templates`) to understand the available capabilities, which can help you formulate more realistic plan steps.
    4.  **Generate Plan Steps:** Create a list of `PlanStepOutput` objects. Each step should:
        -   Have a clear and concise `description` of a strategic phase (e.g., "Perform initial reconnaissance," "Enumerate Active Directory," "Search for sensitive files on discovered shares").
        -   Be assigned a logical `order` number, starting from 1.
        -   Include optional `notes` for additional context if needed.
    5.  **Return the Plan:** Your final output must be a `GeneratedPlan` object containing the complete list of steps.

    **Example:**
    -   If `objectives` is "Achieve Domain Admin" and `current_state` shows "0 credentials", your first steps should focus on reconnaissance and initial access, such as "Enumerate public-facing assets" and "Identify potential phishing targets."
    -   If `current_state` already shows "5 credentials" and "2 active implants", you might skip initial access and start with steps like "Perform internal reconnaissance from existing implants" and "Attempt lateral movement with gathered credentials."
    """


class SupervisorSummary(rg.Model):
    """The final summary provided by the supervisor after a cycle."""

    summary_text: str = rg.element()

    @classmethod
    def xml_example(cls) -> str:
        return cls(
            summary_text="I have analyzed the event and taken the appropriate actions.",
        ).to_pretty_xml()


@generator.prompt
async def update_testing_plan(
    current_plan_summary: str,
    new_event: str,
) -> SupervisorSummary:  # type: ignore
    """You are an expert penetration testing supervisor. Your role is to analyze the current state of a security assessment plan and adapt it based on new events by calling tools.

    **Your Goal:**
    Your primary goal is to advance the plan's main objective. Analyze the provided `current_plan_summary` and the `new_event` (which includes a high-level state summary). Use your tools to modify the plan and create suggestions.

    **Review the Plan:**
    A summary of the current plan steps, their statuses, and any existing suggestions is provided in `current_plan_summary`.
    - **Your primary goal is to build upon this existing plan, not to repeat it.** Do not use `create_plan_step` for actions that are already covered.
    - **Review the 'Existing Suggestions' for each step.** If a suitable suggestion for your intended action already exists, do not create a duplicate.
    - **When creating a new suggestion, you MUST associate it with the most relevant `plan_step_id` from the summary.** For example, a suggestion to run BloodHound should be linked to a plan step like "Enumerate Active Directory."

    **Mandatory Workflow:**
    You MUST follow these steps in order when deciding on an action:

    1.  **Analyze and Decide:** Review the `current_plan_summary` (including existing suggestions) and `new_event` to decide on the next logical action.

    2.  **Discover Playbooks:** If you decide a new suggestion is needed, find the right playbook. You must first discover the available search filters by calling `list_filters(model_name='playbook_template')` to get categories like 'tactic'.

    3.  **Find Specific Playbook:** Use the filters you discovered to call `get_playbook_templates`. Be specific in your search (e.g., `get_playbook_templates(tactic='Discovery')`) to find the correct `playbook_template_id`.

    4.  **Validate Arguments (for EACH target):** Before creating a suggestion, you MUST call `validate_playbook_arguments` with the `playbook_template_id` and the specific `arguments` you intend to use (e.g., `{"c2_implant_id": "..."}`).
        -   **Multiple Targets:** If you want to run the same playbook on 3 different implants, you MUST call `validate_playbook_arguments` 3 separate times, once for each implant's ID.

    5.  **Create Suggestion (for EACH target):** ONLY if `validate_playbook_arguments` returns "Validation successful," you may then call `create_suggestion_for_plan_step` with the exact same arguments.
        -   **Multiple Targets:** Following the example above, you will call `create_suggestion_for_plan_step` 3 separate times.

    6.  **Track Progress:** As you work on a step by creating suggestions, use `update_plan_step` to move its status from 'pending' to 'in_progress'. When a step's objective is fully achieved, mark it as 'completed'.

    **Final Output:**
    After making all necessary tool calls, provide your final response using the `SupervisorSummary` model. Return a brief, one-sentence summary of the actions you took in the `summary_text` field.
    """
