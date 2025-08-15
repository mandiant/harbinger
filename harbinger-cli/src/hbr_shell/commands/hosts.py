from ..utils import make_api_request, print_output

def setup(subparsers):
    """Setup the hosts command."""
    parser = subparsers.add_parser("hosts", help="Manage hosts")
    parser.set_defaults(func=list_hosts)

def list_hosts(args):
    """List all hosts."""
    response = make_api_request("GET", "/hosts/")
    if response:
        hosts_data = response.json()
        hosts = hosts_data.get("items", [])
        headers = ["ID", "Name", "Domain", "OS"]
        
        output_data = []
        for h in hosts:
            output_data.append({
                "id": h.get("id"),
                "name": h.get("name"),
                "domain": h.get("domain"),
                "os": h.get("os"),
            })
        print_output(output_data, headers, args.output)
