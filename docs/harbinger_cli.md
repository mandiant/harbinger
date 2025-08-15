# `hbr` - The Harbinger CLI

The `hbr` command is a powerful, standalone tool for interacting with the Harbinger platform. It allows operators to manage data, control C2 infrastructure, and record terminal sessions as evidence.

## 1. Installation

The `hbr` tool is a standalone package. To install it, navigate to the `harbinger-cli` directory and use `pip`:

```bash
cd /path/to/Harbinger/harbinger-cli
pip install .
```

This will install the `hbr` command and its required dependencies.

## 2. Configuration and Authentication

The `hbr` CLI uses a local configuration file to store your API URL and an authentication cookie. To get started, you must first log in.

### `hbr login`

This command will prompt you for your Harbinger API URL, username, and password.

```bash
hbr login
```

Upon successful authentication, the CLI will store your API URL and an authentication cookie in `~/.harbinger/config`. This cookie will be used for all subsequent commands.

## 3. Global Options

-   `-o, --output {table,json,jsonl}`: Specifies the output format for `list` commands. The default is `table`.

## 4. Available Commands

The `hbr` CLI is organized into a series of subcommands.

### `hbr shell`

Records a terminal session and uploads it to Harbinger.

**Usage:**

```bash
hbr shell
```

This will start a new, nested shell session. All commands you type and all output you see in this shell will be recorded. To stop the recording, simply exit the shell (`exit` or `Ctrl+D`).

After the session ends, you will be prompted to select which of the recorded commands you wish to upload.

### `hbr files`

Manage files in Harbinger.

-   **`hbr files list`**: Lists all uploaded files.
-   **`hbr files upload <file_path> [--file-type <type>]`**: Uploads a file.
-   **`hbr files download <file_id> <output_path>`**: Downloads a file.

### `hbr c2`

Manage C2 infrastructure.

-   **`hbr c2 servers list`**: Lists all configured C2 servers.
-   **`hbr c2 implants list`**: Lists all active C2 implants.
-   **`hbr c2 tasks list`**: Lists all C2 tasks.

### `hbr playbooks`

Manage playbooks.

-   **`hbr playbooks list`**: Lists all available playbooks.

### `hbr proxies`

Manage proxies.

-   **`hbr proxies list`**: Lists all configured proxies.
-   **`hbr proxies jobs list`**: Lists all proxy jobs.

### `hbr domains`

Manage domains.

-   **`hbr domains list`**: Lists all domains.

### `hbr credentials`

Manage credentials.

-   **`hbr credentials list`**: Lists all credentials.

### `hbr hosts`

Manage hosts.

-   **`hbr hosts list`**: Lists all hosts.

### `hbr labels`

Manage labels.

-   **`hbr labels list`**: Lists all labels.