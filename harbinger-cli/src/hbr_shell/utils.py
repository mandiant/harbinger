import configparser
import json
from pathlib import Path

import requests
import urllib3
from tabulate import tabulate

urllib3.disable_warnings()


def get_auth_config():
    """Get API URL and cookie from config file."""
    config_dir = Path.home() / ".harbinger"
    config_file = config_dir / "config"

    if not config_file.exists():
        return None, None

    config = configparser.ConfigParser()
    config.read(config_file)

    api_url = config.get("auth", "api_url", fallback=None)
    cookie = config.get("auth", "cookie", fallback=None)

    return api_url, cookie


def make_api_request(method, endpoint, **kwargs):
    """Make an authenticated API request to Harbinger."""
    api_url, cookie = get_auth_config()
    if not api_url or not cookie:
        print("Error: Not logged in. Please run 'hbr login' first.")
        return None

    url = f"{api_url}{endpoint}"
    cookies = {"fastapiusersauth": cookie}

    try:
        response = requests.request(
            method,
            url,
            cookies=cookies,
            verify=False,
            **kwargs,
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None


def print_output(data, headers, output_format="table"):
    """Print data in the specified format."""
    if output_format == "json":
        print(json.dumps(data, indent=2))
    elif output_format == "jsonl":
        for item in data:
            print(json.dumps(item))
    else:
        table_data = []
        for item in data:
            table_data.append(
                [item.get(header.lower().replace(" ", "_")) for header in headers],
            )
        print(tabulate(table_data, headers=headers))
