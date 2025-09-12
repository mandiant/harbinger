from ..utils import make_api_request, print_output


def setup(subparsers):
    """Setup the labels command."""
    parser = subparsers.add_parser("labels", help="Manage labels")
    parser.set_defaults(func=list_labels)


def list_labels(args):
    """List all labels."""
    response = make_api_request("GET", "/labels/")
    if response:
        labels_data = response.json()
        labels = labels_data.get("items", [])
        headers = ["ID", "Name", "Category", "Color"]

        output_data = []
        for label in labels:
            output_data.append(
                {
                    "id": label.get("id"),
                    "name": label.get("name"),
                    "category": label.get("category"),
                    "color": label.get("color"),
                },
            )
        print_output(output_data, headers, args.output)
