# `hbr-shell` - Harbinger Shell Recorder

The `hbr-shell` command is a standalone tool that allows operators to record their terminal sessions and automatically upload them to Harbinger as evidence.

## 1. Installation

The `hbr-shell` tool is a standalone package. To install it, navigate to the `harbinger-cli` directory and use `pip`:

```bash
cd /path/to/Harbinger/harbinger-cli
pip install .
```

This will install the `hbr-shell` command and its required dependencies.

It has one external dependency:

*   **`asciinema`**: This is the underlying recording engine. You must install it on your system.

Please refer to the [Development Setup](./development_setup.md) guide for instructions on installing `asciinema`.

## 2. Configuration

Before using the tool, you must configure it by setting two environment variables:

*   `HBR_API_URL`: The full URL to your Harbinger API.
    *   Example: `export HBR_API_URL="http://localhost:8000"`
*   `HBR_API_TOKEN`: Your personal API token for authenticating with the Harbinger API.
    *   Example: `export HBR_API_TOKEN="your_secret_token_here"`

It is recommended to add these `export` commands to your shell's profile file (e.g., `~/.bashrc`, `~/.zshrc`) so they are always available.

## 3. Usage

To start a recording, simply run the command in your terminal:

```bash
hbr-shell
```

This will start a new, nested shell session. All commands you type and all output you see in this shell will be recorded.

To stop the recording, simply exit the shell:

```bash
exit
```

After you exit, the tool will launch an interactive prompt where you can select which of the recorded commands you wish to upload.

```
Select commands to upload to Harbinger:
(Press <space> to select, <a> to select all, <i> to invert, <enter> to confirm)

[x] 1. whoami
[ ] 2. ls -la
[x] 3. cat /etc/passwd
```

After selecting the commands, you will be prompted to provide a high-level description for the set of actions.

The tool will then upload each selected command as a separate recording, each linked to its own timeline event.

## 4. Integration with Harbinger

For each command you select for upload:

1.  A new `ManualTimelineTask` is created in Harbinger. The command itself is used as the title, and the description you provided is added.
2.  A new entry is created in the **Files** section of the Harbinger UI. The file will have the type `cast` and will contain only the single command and its output.
3.  This file is linked to the timeline event, providing a clear and granular audit trail of the activity.
