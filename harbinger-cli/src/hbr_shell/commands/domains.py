from ..utils import make_api_request, print_output

def setup(subparsers):
    """Setup the domains command."""
    parser = subparsers.add_parser("domains", help="Manage domains")
    parser.set_defaults(func=list_domains)

def list_domains(args):
    """List all domains."""
    response = make_api_request("GET", "/domains/")
    if response:
        domains_data = response.json()
        domains = domains_data.get("items", [])
        headers = ["ID", "Short Name", "Long Name"]
        
        output_data = []
        for d in domains:
            output_data.append({
                "id": d.get("id"),
                "short_name": d.get("short_name"),
                "long_name": d.get("long_name"),
            })
        print_output(output_data, headers, args.output)
