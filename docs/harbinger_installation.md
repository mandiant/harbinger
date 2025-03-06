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
  vars:
    users:
    - user1
    neo4j_host: 10.10.10.2
    neo4j_port: 7687
    neo4j_user: neo4j
    neo4j_password: neo4j_password_here
    # if you want to enable gemini based processing, leave empty if not needed
    gemini_api_key: api_key_here
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
    neo4j_host: 10.10.10.2
    neo4j_port: 7687
    neo4j_user: neo4j
    neo4j_password: neo4j_password_here
    # if you want to enable gemini based processing, leave empty if not needed
    gemini_api_key: api_key_here
```

Run the ansible playbook:

```bash
ansible-playbook -i inventory.yaml complete.harbinger.yaml
```

This should take some time, afterwards ssh into harbinger and port forward 8443:

```
ssh -L 8443:localhost:8443 debian@10.10.10.1
```

Even better create a ssh config:

```.ssh/config
Host harbinger
    Hostname 10.10.10.1
    User debian
    LocalForward 8443 localhost:8443
    LocalForward 2200 localhost:2200
```

Afterwards login to your server on [https://localhost:8443](https://localhost:8443). Make sure to use a hostname to connect, if you connect by IP it will not work. Login with the password from `site/harbinger1/harbinger_password.txt`
