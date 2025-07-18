# Development setup

Have an ubuntu vm with docker compose installed. Add your current user to the docker group with the next command:

```bash
sudo usermod -aG docker $USER
```

Start a neo4j server with the following docker command:

```bash
docker run --restart unless-stopped --publish=7474:7474 --publish=7687:7687 --name neo4j -e NEO4J_apoc_export_file_enabled=true -e NEO4J_apoc_import_file_enabled=true -e NEO4J_apoc_import_file_use__neo4j__config=true -e NEO4JLABS_PLUGINS=\[\"apoc\"\] -e NEO4J_AUTH=neo4j/test -d neo4j:4.4.16
```

Run the setup_harbinger.py file and fill in the values.

```bash
python3 harbinger/src/harbinger/scripts/setup_harbinger.py
```

This will create the environment files for you.

Use the devcontainers plugin of vscode to start your development environment.

The first time create a virtual environment with python and install harbinger:

```bash
cd harbinger
python -m venv venv
source venv/bin/activate
pip install -r requirements_dev.txt --no-deps
pip install -r requirements.txt --no-deps
pip install -e . --no-deps
```

Run the migrations and other tools for the first time:

```bash
harbinger_migrate
harbinger_create_user --username {your_username} --password {your_password}
harbinger_create_defaults
```

For the frontend cd to the `interface` directory and run npm install.

```bash
cd interface
npm install
```

Use [task](https://taskfile.dev) to start all the components in different terminals, for the python components first activate the venv:

```bash
source harbinger/venv/bin/activate # Do this for every new terminal
task frontend
task uvicorn/reload
task worker
task grpc
task worker/docker
```

Or start the components manually in other terminals:

```bash
uvicorn harbinger.config.app:app --reload --host 0.0.0.0
harbinger_worker
harbinger_docker_worker
harbinger_grpc

# in the harbinger/interface directory
quasar dev
```

To login browse to the [interface](https://localhost:9002) and login. The API requires its own login, for this go to the [fast api swagger page](http://localhost:8000/docs#/auth/auth_redis_login_auth_login_post) and login.

## Troubleshooting

### Temporary failure resolving in docker

If you get errors like "Temporary failure resolving". Then hardcode a DNS server in the docker config (`/etc/docker/daemon.json`):

```
{
    "dns": ["1.1.1.1"]
}
```

### "quasar": executable file not found in $PATH

Quasar was not installed correctly use the next command to install:

```bash
npm install -g @quasar/cli
```
