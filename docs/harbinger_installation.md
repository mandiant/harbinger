# Harbinger installation

Harbinger installation is based on an ansible role in this repository.
First clone this repository.

Create a virtualenv and install ansible in it:

```bash
cd ansible
python3 -m virtualenv venv
source venv/bin/activate
pip install ansible
```

Then install the required roles:

```bash
ansible-galaxy install geerlingguy.docker
ansible-galaxy collection install community.docker
ansible-galaxy collection install community.crypto
```

Create your inventory file like the following:

```yaml
harbinger_server:
  hosts:
    harbinger1:
      ansible_user: debian
      ansible_host: 10.10.10.1
      ansible_password: debian
      # Optionally upload config files into harbinger
      harbinger_files_to_upload:
      - src_path: "~/config.yaml"
        filetype: "harbinger_yaml"
  vars:
    users:
    - user1
    harbinger_neo4j_host: 10.10.10.2
    harbinger_neo4j_port: 7687
    harbinger_neo4j_user: neo4j
    harbinger_neo4j_password: neo4j_password_here
    # if you want to enable gemini based processing, leave empty if not needed
    harbinger_gemini_key: api_key_here
    # Change the hostname, will default to your inventory name.
    harbinger_domain_name: harbinger1.local
    # Change from this value if you want it to listen on another port
    harbinger_listen_port: 8443
    # Swap to true if docker and docker compose are already installed
    harbinger_skip_docker_installation: false
```

If you want to install it on the local vm use this in your inventory:

```yaml
harbinger_server:
  hosts:
    harbinger1:
      ansible_user: your-local-username
      ansible_host: localhost
      ansible_password: local-user-password-here
      ansible_connection: local
  vars:
    users:
    - example
    harbinger_neo4j_host: 10.10.10.2
    harbinger_neo4j_port: 7687
    harbinger_neo4j_user: neo4j
    harbinger_neo4j_password: neo4j_password_here
    # if you want to enable gemini based processing, leave empty if not needed
    harbinger_gemini_key: api_key_here
```

Run the ansible playbook:

```bash
ansible-playbook -i inventory.yaml complete.harbinger.yaml
```

Afterwards login to your server on [https://harbinger1:8443](https://harbinger1:8443). Make sure to use your specified hostname to connect. Login with the password from `site/harbinger1/harbinger_password.txt` with the user you've specified in your inventory file.
