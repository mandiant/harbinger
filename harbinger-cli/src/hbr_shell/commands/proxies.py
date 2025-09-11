from ..utils import make_api_request, print_output


def setup(subparsers):
    """Setup the proxies command."""
    parser = subparsers.add_parser("proxies", help="Manage proxies")
    proxies_subparsers = parser.add_subparsers(dest="proxies_command", required=True)

    # List command
    list_parser = proxies_subparsers.add_parser("list", help="List all proxies")
    list_parser.set_defaults(func=list_proxies)

    # Jobs list command
    jobs_list_parser = proxies_subparsers.add_parser("jobs", help="List proxy jobs")
    jobs_list_parser.set_defaults(func=list_proxy_jobs)


def list_proxies(args):
    """List all proxies."""
    response = make_api_request("GET", "/proxies/")
    if response:
        proxies_data = response.json()
        proxies = proxies_data.get("items", [])
        headers = ["ID", "Type", "Host", "Port", "Status"]

        output_data = []
        for p in proxies:
            output_data.append(
                {
                    "id": p.get("id"),
                    "type": p.get("type"),
                    "host": p.get("host"),
                    "port": p.get("port"),
                    "status": p.get("status"),
                }
            )
        print_output(output_data, headers, args.output)


def list_proxy_jobs(args):
    """List proxy jobs."""
    response = make_api_request("GET", f"/proxy_jobs/")
    if response:
        jobs_data = response.json()
        jobs = jobs_data.get("items", [])
        headers = ["ID", "Command", "Status", "Time Created"]

        output_data = []
        for j in jobs:
            output_data.append(
                {
                    "id": j.get("id"),
                    "command": j.get("command"),
                    "status": j.get("status"),
                    "time_created": j.get("time_created"),
                }
            )
        print_output(output_data, headers, args.output)
