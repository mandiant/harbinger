from ..utils import make_api_request, print_output


def setup(subparsers):
    """Setup the credentials command."""
    parser = subparsers.add_parser("credentials", help="Manage credentials")
    parser.set_defaults(func=list_credentials)


def list_credentials(args):
    """List all credentials."""
    response = make_api_request("GET", "/credentials/")
    if response:
        credentials_data = response.json()
        credentials = credentials_data.get("items", [])
        headers = ["ID", "Username", "Domain", "Password"]

        output_data = []
        for c in credentials:
            output_data.append(
                {
                    "id": c.get("id"),
                    "username": c.get("username"),
                    "domain": c.get("domain").get("long_name")
                    if c.get("domain")
                    else "",
                    "password": c.get("password").get("password")
                    if c.get("password")
                    else "",
                },
            )
        print_output(output_data, headers, args.output)
