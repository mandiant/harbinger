

PLAYBOOK_FORMAT_DESCRIPTION = """
This is the Harbinger playbook template format:

id: <unique_playbook_id>  # Replace with a unique ID (UUID recommended)
name: '<Playbook Name>' # Give your playbook a descriptive name, quote it to make sure you can include ':' symbols.
icon: <icon_name>  # Choose an icon (refer to the material icons library)
tactic: <mitre_attack_tactic>  # Specify the MITRE ATT&CK tactic
technique: <mitre_attack_technique>  # Specify the MITRE ATT&CK technique
labels: [<label1>, <label2>, ...]  # Add relevant labels (e.g., "Network," "Exfiltration")
add_depends_on: <yes/no>  # If "yes," Harbinger adds depends_on to steps

args:  # Define input arguments for the playbook
    - name: <argument_name>
    type: <argument_type>  # (e.g., str, int, list)
    description: '<argument_description>' # make sure you quote this.
    default: <default_value>  # (optional)

steps: |  # Define the steps using YAML or Jinja2 templating
    - type: <step_type>  # (e.g., c2, delay, runassembly)
    name: <step_name>  # (e.g., run, sleep, download)
    args:  # Arguments for the step
        - name: <argument_name>
        value: <argument_value> 
    label: <step_label>  # (optional)
    depends_on: <previous_step_label>  # (optional)

Explanation:
id: A unique identifier for the playbook. Use a UUID for best practice.
name: A descriptive name for the playbook.
icon: An icon to represent the playbook (refer to Harbinger's documentation for available icons).
tactic and technique: These categorize the playbook within the MITRE ATT&CK framework.
labels: Add relevant tags or classifications.
add_depends_on: If set to "yes," Harbinger automatically adds depends_on to the steps, creating a sequential workflow.
args: Define the input arguments for your playbook. You can specify the argument's name, type, description, and default value.
steps: This section defines the actions to be executed.
type: The type of step (e.g., c2 for a command to your C2 server).
name: The specific command or action to be executed.
args: Arguments for the step.
label and depends_on: Used for controlling the workflow and dependencies between steps.

# Creating playbook templates

Playbooks are a sequence of steps that are executed on a c2 server or via a proxy. To make it easier for operator, Harbinger supports playbook templates. These are templated playbooks where Harbinger requests information from the operator and renders the template steps afterwards. For example if you want to use nanodump without the nanodump cna file. It requires input in the following format: `i:0 z: i:0 i:0 i:0 i:0 i:0 i:0 i:0 i:0 i:0 i:0 z: i:0 i:0 i:0 z: i:0`. This format is not super understandable for operators. If you use the example nanodump template, Harbinger renders it as follows:

Next up is an example playbook that includes the options you can use in a playbook template, afterwards special argument names are showed that will retrieve data from, for example, Neo4j.

## Example playbook

A playbook is show below with comments on what each part does:

```yaml
# The ID of this playbook, must be a guid and unique, don't reuse this
id: 0e3ad568-5fa5-4be8-bd27-8d9abf341f2b
# Icon to show in the interface. Can be any of the material icons.
icon: new
# Name to display in the interface.
name: "Sleep test"
# for a simple lineair pipeline set to yes, if set to no make sure you specify the labels and depends on for the required steps.
add_depends_on: yes

# Arguments that are validated and passed to each step.
# Make sure to include all arguments that each step uses in this argument list or in the steps below, otherwise it will not be possible to use this template.
# Some special names can be used that will render differently in the interface, see the table below.
args:
  - name: c2_implant_id
    # valid options are str, bool, int and options.
    type: str
  - name: max
    type: int
    # set a default
    default: 10
  - name: choose
    type: options
    options:
    - number1
    - number2
    - number3
    # must be filled in.
    required: true

# The steps of this playbook. Make sure to include the "|", because this will be rendered with jinja to make the separate steps.
steps: |
  # Step 1 of this playbook, make sure the type and name combination exists.
  - type: c2
    name: sleep
    # Optional label to identify this step in the playbook
    label: A
    # This step can depend on other steps, if they don't exists it will be skipped, separate multiple with a comma.
    depends_on: B
    # Delay in seconds
    delay: 10
    # Extra argument specifically for this step.
    # These arguments will only be used for rendering the command of this step 
    args:
      - name: sleep
        value: 0
  # normal jinja2 syntax can be used like loops:
  {% for i in range(max) %}
  - type: c2
    name: sleep
    args:
      - name: sleep
        value: {{ i }}
  {% endfor %}
```

## Longer example

This playbook includes most commands that can be done on a c2 implant. Also shows how to select multiple files and how to pass the file_id correctly to each step. The c2_implant value is implicitly passed to all c2 steps.

```yaml
id: ce868a7b-9190-4e9d-88e8-4bfd7fa514c1
icon: cruelty_free
name: 'test all commands playbook'
step_delay: 0
add_depends_on: yes

args:
- name: c2_implant
  type: str
- name: sleep
  type: int
  default: 10
- name: jitter
  type: int
  default: 20
- name: file_id
  type: str
  default: e4a933f4-2157-4918-ab5e-26506af1cd3c
- name: file_id_2
  type: str
  default: 292557b2-7d1c-4a3c-8cd9-7ec8cbb24545
  filetype: exe
- name: file_id_3
  type: str
  default: 03927435-7b5b-4e13-bf39-226fac608c99
  filetype: bof

steps: |
  - type: c2
    name: sleep
    args:
      - name: sleep
        value: {{ sleep }}
      - name: jitter
        value: {{ jitter }}
  - type: c2
    name: ps
  - type: c2
    name: shell
    args:
      - name: command
        value: ipconfig
  - type: c2
    name: ls
  - type: c2
    name: download
    args:
      - name: path
        value: test.txt
  - type: c2
    name: cp
    args:
      - name: source
        value: test.txt
      - name: destination
        value: test2.txt
  - type: c2
    name: rm
    args:
      - name: path
        value: test2.txt
  - type: c2
    name: upload
    args:
      - name: file_id
        value: {{ file_id }}
      - name: remotename
        value: test3.txt
  - type: c2
    name: runassembly
    args:
      - name: arguments_str
        value: test
      - name: file_id
        value: {{ file_id_2 }}
  - type: c2
    name: runbof
    args:
      - name: file_id
        value: {{ file_id_3 }}
  - type: c2
    name: mkdir
    args:
      - name: path
        value: "thispathhopefullydoesntexistsyet"
  - type: c2
    name: mv
    args:
      - name: source
        value: test3.txt
      - name: destination
        value: test4.txt
  - type: c2
    name: pwd
  - type: c2
    name: runprocess
    args:
      - name: command
        value: calc.exe
```

## Socks

For socks you can pick one of the predefined steps or use the `custom` task name. This task takes a `command` and `arguments` parameter.

```
id: b6bc6a59-94b8-418d-b418-36c82692617c
icon: add
name: 'Test socks proxy playbook'
step_delay: 0

args:
- name: argument0
  type: str
  default: argument0
- name: argument1
  type: str
  default: argument1

steps: |
  - type: socks
    name: custom
    args:
      - name: command
        value: {{ argument0 }}
      - name: arguments
        value: {{ argument1 }}
```

## Special arguments

Certain fields are automatically converted to components that select specific data from the database. The next table shows some examples.

| Argumentname             | Description                                                     |
| ------------------------ | --------------------------------------------------------------- |
| target_computer          | Search / Dropdown to select a computer name from neo4j          |
| target_domain_controller | Search / Dropdown to select a domain controller name from neo4j |
| c2_implant               | Shows a dropdown to select an implant                           |
| target_user              | Search / dropdown to select a user name from neo4j              |
| target_group             | Search / dropdown to select a group name from neo4j             |
| credential_id            | Shows a dropdown to select a credential                         |
| file_id                  | Shows a dropdown to select a file                               |
| proxy_id                 | Shows a dropdown to select a proxy                              |


If the command is not part of this enum then use the custom socks type:

class Command(str, Enum):
    ps = "ps"
    ls = "ls"
    download = "download"
    sleep = "sleep"
    rm = "rm"
    upload = "upload"
    runassembly = "runassembly"
    runbof = "runbof"
    cp = "cp"
    cd = "cd"
    mkdir = "mkdir"
    mv = "mv"
    pwd = "pwd"
    runprocess = "runprocess"
    socks = "socks"
    exit = "exit"
    shell = "shell"
    disableetw = "disableetw"
    disableamsi = "disableamsi"
    unhook = "unhook"

"""

PLAYBOOK_EXAMPLES = """
id: 1d07daed-89ab-403a-b94a-26ae4b5565c8
name: 'Kerbrute-Python'
tactic: credential access
technique: brute force
labels: ["Socks"]
icon: fas fa-staff-snake
add_depends_on: 'no'
args:
- name: proxy_id
    type: str
- name: password
    type: str
    description: 'Password to use for spraying'
- name: domain
    type: str
- name: filename
    type: str

steps: |
    - type: socks
    name: custom
    args:
    - name: command
        value: kerbrute
    - name: arguments
        value: "-domain {{ domain }} -users {{ filename }} -passwords {{ password }} -outputfile {{ domain }}_passwords.txt"
    label: A

This is another example of a playbook:

id: ca778dec-c7f6-4be8-8015-aa90950c1867
name: 'BloodHound.py'
icon: fa-solid fa-paw
add_depends_on: 'no'
tactic: discovery
technique: bloodhound
labels: ["Socks"]
args:
- name: credential_id
    type: str
- name: domain
    type: str
- name: collection_method
    type: options
    default: DCOnly
    options:
    - Container
    - Group
    - LocalGroup
    - GPOLocalGroup,
    - Session
    - LoggedOn
    - ObjectProps
    - ACL
    - ComputerOnly
    - Trusts
    - Default
    - RDP
    - DCOM
    - DCOnly
    - All
- name: auth_method
    type: options
    default: auto
    options:
    - auto
    - kerberos
    - ntlm
- name: dns_server
    type: str
    default: ''
- name: target_domain_controller
    type: str
    default: ''
- name: proxy_id
    type: str
- name: socks_server_id
    type: str
    default: dfe9668d-fda8-4f96-a4b4-b4db843a7b02
- name: ldaps
    type: bool
    default: true
steps: |
    - type: socks
    name: custom
    args:
    - name: command
        value: bloodhound-python
    - name: arguments
        value: -c {{ collection_method }} -u {{ credential.username }}@{{ credential.domain.long_name }}{% if credential.password.password %} -p '{{ credential.password.password }}'{% endif %}{% if credential.password.nt %} --hashes :{{ credential.password.nt }} {% endif %}{% if credential.password.kerberos %}-k{% endif %} --dns-tcp{% if dns_server %} -ns {{ dns_server }}{% endif %} --disable-autogc --auth-method {{ auth_method }}{% if ldaps %} --use-ldaps{% endif %}{% if target_domain_controller %} -dc {{ target_domain_controller }} -gc {{ target_domain_controller }}{% endif %} --domain {{ domain }}
    label: A
    depends_on: ''


This is an example for runbof, this example should be used if a CNA script is passed and a bof is loaded:
files:
  - id: fc40e7c3-306e-4c6c-9ce8-d1fed09bcb2a
    path: bin/nanodump.x64.o
    name: nanodump.x64.o
    type: bof
  - id: 1c5e25de-c439-4e2b-b08c-23921d5da2e3
    path: bin/nanodump.x86.o
    name: nanodump.x86.o
    type: bof
playbooks:
  - id: 652f14db-ab96-402f-a200-6053f975dda5
    icon: add
    tactic: credential access
    technique: lsass memory
    labels: ["Bof"]
    name: "Nanodump"

    args:
      - name: c2_implant_id
        type: str
      - name: file_id
        type: str
        default: fc40e7c3-306e-4c6c-9ce8-d1fed09bcb2a
        filetype: bof
      - name: pid
        type: int
        default: 0
      - name: path
        type: str
        default: ""
      - name: write_file
        type: bool
        default: False
      - name: chunk_size
        type: int
        default: 921600
      - name: use_valid_sig
        type: bool
        default: False
      - name: fork
        type: bool
        default: False
      - name: snapshot
        type: bool
        default: False
      - name: dup
        type: bool
        default: False
      - name: elevate_handle
        type: bool
        default: False
      - name: duplicate_elevate
        type: bool
        default: False
      - name: get_pid
        type: bool
        default: False
      - name: use_seclogon_leak_local
        type: bool
        default: False
      - name: use_seclogon_leak_remote
        type: bool
        default: False
      - name: seclogon_leak_remote_binary
        type: str
        default: ""
      - name: use_seclogon_duplicate
        type: bool
        default: False
      - name: spoof_callstack
        type: bool
        default: False
      - name: use_silent_process_exit
        type: bool
        default: False
      - name: silent_process_exit
        type: str
        default: ""
      - name: use_lsass_shtinkering
        type: bool
        default: False

    steps: |
      - type: c2
        name: runbof
        args:
          - name: arguments_str
            value: 'i:{{ pid }} z:{{ path or '' }} i:{{ write_file | int }} i:{{ chunk_size }} i:{{ use_valid_sig | int }} i:{{ fork | int }} i:{{ snapshot | int }} i:{{ dup | int }} i:{{ elevate_handle | int }} i:{{ duplicate_elevate | int }} i:{{ get_pid | int }} i:{{ use_seclogon_leak_local | int }} i:{{ use_seclogon_leak_remote | int }} z:{{ seclogon_leak_remote_binary or '' }} i:{{ use_seclogon_duplicate | int }} i:{{ spoof_callstack | int }} i:{{ use_silent_process_exit | int }} z:{{ silent_process_exit or '' }} i:{{ use_lsass_shtinkering | int }}'
"""