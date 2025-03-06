# Harbinger Configuration

Harbinger has functionality upload files and parse them. This functionality is used to import harbinger specific data. You can upload one a file with the type `harbinger_yaml` or create a zip file with one or more files called `*harbinger.yaml` to automatically import and configure harbinger.

The following data can be loaded by harbinger from these files:

* Playbook templates
* C2 Connectors
* Actions
* Labels
* Files

Each harbinger yaml file can contain one or more of the following keys, each with potential multiple items:

* playbooks
* c2_server_types
* actions
* labels
* files

Always make sure your `id` fields in the yaml files are unique `UUID4` identifiers. These are used to deduplicate data and to reference other items. If they are not defined or unknown it can mess up the import process.

With python you can create unique ids like this:

```bash
python3 -c 'import uuid;print(str(uuid.uuid4()))'
```


## Playbooks

The playbook itself is wrapped in a key called playbooks. You can put any number of playbooks in this list.
See [Creating playbooks](creating_playbooks.md) how how to construct your playbook template.

```yaml
playbooks:
  - id: b13e64a7-5623-4d69-bb6e-5718b887658c
    name: List multiple directories
    icon: fas fa-sitemap
    tactic: reconnaissance
    technique: gather victim host information
    add_depends_on: 'yes'
    labels: ["Built-in"]
    args:
    - name: c2_implant_id
      type: str
    - name: directories
      type: str
      description: Directories to list, separated by '|'
    steps: |
      {% for directory in directories.split("|")%}
      - type: c2
        name: ls
        args:
        - name: folder
          value: '{{directory}}'
        - name: c2_implant_id
          value: '{{ c2_implant_id }}'
      {% endfor %}
```


## C2 Connectors

If you want to connect to another c2 server. You can create a c2 connector for you server and instruct harbinger to use it.


```yaml
c2_server_types:
  - id: 3a7c34bb-93d9-4200-a5dd-36d199a2b171
    name: mythic
    docker_image: harbinger_mythic:latest
    command: harbinger_mythic_client
    required_arguments:
      - name: password
      - name: username
        default: mythic_admin
      - name: hostname
      - name: port
        default: 7443
```

See [custom connectors](custom_connectors.md) on how to make your custom c2 connector.


## Actions

Actions are basically a checklist of actions that you want to perform. Each action can have one or more playbook template ids. If one of the playbooks is executed, the action will be crossed off.

An example is shown below.

```yaml
actions:
  - id: "571d3167-9986-48fb-9b01-a5f019695f9c"
    name: "AD Reconnaissance"
    description: "Perform AD reconnaissance with sharphound, adexplorer or others."
    playbook_template_ids:
    - ac7a5098-b63d-46f1-8b76-2824415bce6b
    - 997ba59b-857f-45cd-abb8-dcf39f9816c4
    labels: ["Purple Team"]
```

Make sure the `playbook_template_ids` are defined somehow, can be done via the interface or you can put the actions and playbooks into one yaml file. If the label doesn't exist yet, it will be created.

## Labels

Labels are used to organise the data and these can be used to filter the data in the interface. You can define labels like this:


```yaml
labels:
  - id: 8d1c22cc-29eb-4b6c-b0f1-471b4a8885a7
    name: Red Team
    category: Playbooks
    color: "#FF0000"
  - id: 26a56f12-0086-4def-a639-60481936133b
    name: Purple Team
    category: Playbooks
    color: "#5200A3"
```

If the color is not set, a random color will be created.


## Files

Files are only loaded if you uploaded a zip with one or more `*harbinger.yaml` files in there. Make sure to reference the files in the zip in your yaml file like the following:

```yaml
files:
  - id: e83a7088-6110-483e-b576-a38da64272b1
    path: bin/test.x64.o
    name: test.x64.o
    type: bof
  - id: 784c1ba5-97a3-4044-8b99-d3ca12adf6a3
    path: bin/adexplorer.exe
    name: adexplorer.exe
    type: exe
```

Make sure the `id` field is unique and the `path` field points to the file in the zip. The `name` is shown in the interface and the `type` field is used to determine what kind of file it is.

