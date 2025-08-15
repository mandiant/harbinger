from ..utils import make_api_request, print_output

def setup(subparsers):
    """Setup the playbooks command."""
    parser = subparsers.add_parser("playbooks", help="Manage playbooks")
    playbooks_subparsers = parser.add_subparsers(dest="playbooks_command", required=True)

    # List command
    list_parser = playbooks_subparsers.add_parser("list", help="List all playbooks")
    list_parser.set_defaults(func=list_playbooks)

def list_playbooks(args):
    """List all playbooks."""
    response = make_api_request("GET", "/playbooks/")
    if response:
        playbooks_data = response.json()
        playbooks = playbooks_data.get("items", [])
        headers = ["ID", "Name", "Description", "Status"]
        
        output_data = []
        for p in playbooks:
            output_data.append({
                "id": p.get("id"),
                "name": p.get("playbook_name"),
                "description": p.get("description"),
                "status": p.get("status"),
            })
        print_output(output_data, headers, args.output)
