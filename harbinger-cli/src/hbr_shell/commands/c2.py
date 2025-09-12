from ..utils import make_api_request, print_output


def setup(subparsers):
    """Setup the c2 command."""
    parser = subparsers.add_parser("c2", help="Manage C2 infrastructure")
    c2_subparsers = parser.add_subparsers(dest="c2_command", required=True)

    # Servers list command
    servers_list_parser = c2_subparsers.add_parser("servers", help="List C2 servers")
    servers_list_parser.set_defaults(func=list_servers)

    # Implants list command
    implants_list_parser = c2_subparsers.add_parser("implants", help="List C2 implants")
    implants_list_parser.set_defaults(func=list_implants)

    # Tasks list command
    tasks_list_parser = c2_subparsers.add_parser("tasks", help="List C2 tasks")
    tasks_list_parser.set_defaults(func=list_tasks)


def list_servers(args):
    """List C2 servers."""
    response = make_api_request("GET", "/c2_servers/")
    if response:
        servers_data = response.json()
        servers = servers_data.get("items", [])
        headers = ["ID", "Name", "Type", "Hostname", "Status"]

        output_data = []
        for s in servers:
            output_data.append(
                {
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "type": s.get("type"),
                    "hostname": s.get("hostname"),
                    "status": s.get("status")[0].get("status")
                    if s.get("status")
                    else "",
                },
            )
        print_output(output_data, headers, args.output)


def list_implants(args):
    """List C2 implants."""
    response = make_api_request("GET", "/c2_implants/")
    if response:
        implants_data = response.json()
        implants = implants_data.get("items", [])
        headers = ["ID", "Hostname", "OS", "Last Check-in"]

        output_data = []
        for i in implants:
            output_data.append(
                {
                    "id": i.get("id"),
                    "hostname": i.get("hostname"),
                    "os": i.get("os"),
                    "last_check-in": i.get("last_checkin"),
                },
            )
        print_output(output_data, headers, args.output)


def list_tasks(args):
    """List C2 tasks."""
    response = make_api_request("GET", "/c2/tasks/")
    if response:
        tasks_data = response.json()
        tasks = tasks_data.get("items", [])
        headers = ["ID", "Command", "Status", "Time Created"]

        output_data = []
        for t in tasks:
            output_data.append(
                {
                    "id": t.get("id"),
                    "command": t.get("command_name"),
                    "status": t.get("status"),
                    "time_created": t.get("time_created"),
                },
            )
        print_output(output_data, headers, args.output)
