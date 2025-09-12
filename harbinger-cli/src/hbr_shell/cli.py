import argparse

from .commands import (
    c2,
    credentials,
    domains,
    files,
    hosts,
    labels,
    login,
    playbooks,
    proxies,
    shell,
)


def main():
    """Main entry point for the hbr CLI."""
    parser = argparse.ArgumentParser(description="Harbinger CLI")
    parser.add_argument(
        "-o",
        "--output",
        choices=["table", "json", "jsonl"],
        default="table",
        help="Output format",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Login command
    login.setup(subparsers)

    # Shell command
    shell.setup(subparsers)

    # Files command
    files.setup(subparsers)

    # C2 command
    c2.setup(subparsers)

    # Playbooks command
    playbooks.setup(subparsers)

    # Proxies command
    proxies.setup(subparsers)

    # Domains command
    domains.setup(subparsers)

    # Credentials command
    credentials.setup(subparsers)

    # Hosts command
    hosts.setup(subparsers)

    # Labels command
    labels.setup(subparsers)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
