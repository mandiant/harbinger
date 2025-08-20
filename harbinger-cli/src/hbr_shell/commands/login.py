import os
import requests
import configparser
from pathlib import Path

def setup(subparsers):
    """Setup the login command."""
    parser = subparsers.add_parser("login", help="Login to Harbinger")
    parser.add_argument("--api-url", help="Harbinger API URL")
    parser.add_argument("--username", help="Username")
    parser.add_argument("--password", help="Password")
    parser.set_defaults(func=run)

def run(args):
    """Login to Harbinger and save the cookie."""
    api_url = args.api_url or os.environ.get("HBR_API_URL")
    if not api_url:
        api_url = input("Enter Harbinger API URL: ")
    api_url = api_url.rstrip('/')

    username = args.username or input("Username: ")
    password = args.password or input("Password: ")

    try:
        response = requests.post(
            f"{api_url}/auth/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            verify=False,
        )
        response.raise_for_status()

        cookie = response.cookies.get("fastapiusersauth")
        if not cookie:
            print("Login failed: No cookie received.")
            return

        config_dir = Path.home() / ".harbinger"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config"

        config = configparser.ConfigParser()
        if config_file.exists():
            config.read(config_file)
        
        if 'auth' not in config:
            config['auth'] = {}
        
        config['auth']['cookie'] = cookie
        config['auth']['api_url'] = api_url

        with open(config_file, 'w') as f:
            config.write(f)

        print("Login successful. Cookie saved.")

    except requests.exceptions.RequestException as e:
        print(f"Login failed: {e}")
