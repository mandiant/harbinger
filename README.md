# Harbinger

Connecting the different components of red teaming. This project integrates multiple components commonly used in red teaming and makes it easier to perform actions, log output and parse files.

## Features

- **Socks tasks:** Run tools over socks proxies and log the output, as well as templating of commonly used tools.
- **Neo4j:** Use data from neo4j directly into templating of tool commands.
- **C2 Servers:** By default we have support for Mythic. But you can bring your own integration by implementing some code, see the [custom connectors](docs/custom_connector.md) documentation.
- **File parsing:** Harbinger can parse a number of filetypes and import the data into the database. Examples include lsass dumps and ad snapshots. See the [parser table](docs/parsers.md) for a full list.
- **Output parsing:** Harbinger can detect useful information in output from the C2 and provide you easy access to it.
- **Data searching:** Harbinger gives you the ability to search for data in the database in a number of ways. It combines the data from all your C2s in a single database.
- **Playbooks:** Execute commands in turn in a playbook.
- **Darkmode:** Do I need to say more.
- **AI integration:** Harbinger uses LLMs to analyze data, extract useful information and provide suggestions to the operator for the next steps and acts as an assistant.

## Installation
See the [installation](docs/harbinger_installation.md) page for more information.

## Configuration
See the [configuration](docs/configuration.md) page for more information.

## Creating a new playbook template
A big feature of Harbinger is templating of playbooks. See the [creating playbooks](docs/creating_playbooks.md) page for more information about playbook templates.

## Development setup
If you want to setup a development environment, see the [development setup](docs/development_setup.md) page for more information.

## Harbinger CLI

Harbinger includes a powerful command-line interface (`hbr`) to interact with the platform, manage data, and record terminal sessions. See the [`hbr` CLI documentation](docs/harbinger_cli.md) for more information.
