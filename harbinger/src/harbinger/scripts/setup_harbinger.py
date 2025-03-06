# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from getpass import getpass
import secrets
import string
import pathlib
import subprocess


def generate_password(n=20):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))



SERVER_TEMPLATE = """REDIS_DSN=redis://:{redis_password}@redis:6379/0
PG_DSN=postgresql+asyncpg://postgres:{postgres_password}@postgres:5432/postgres
MINIO_HOST=http://minio:9000
MINIO_SSL=false
MINIO_DEFAULT_BUCKET=data
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY={minio_secret_key}
NEO4J_HOST=bolt://{neo4j_host}:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD={neo4j_password}
TEMPORAL_HOST=temporal:7233
"""

PROXY_TEMPLATE = """
RSA_SIG={rsa_sig}
ED25519_SIG={ed25519_sig}
TMATE_SERVER=tmate
TMATE_PORT=2200
"""

MINIO_TEMPLATE = """MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY={minio_secret_key}"""


def main() -> int:
    print("Setting up harbinger")
    deploy = pathlib.Path(__file__).parents[4] / "deploy"
    deploy.mkdir(exist_ok=True)

    keys = deploy / "keys"
    keys.mkdir(parents=True, exist_ok=True)

    ed25519 = keys / "ssh_host_ed25519_key"
    if not ed25519.exists():
        print("Creating ed25519 key")
        subprocess.check_call(
            ["ssh-keygen", "-t", "ed25519", "-f", f"{ed25519}", "-N", ""]
        )

    ed25519_sig = subprocess.check_output(
        ["ssh-keygen", "-l", "-E", "SHA256", "-f", f"{ed25519}.pub"]
    ).decode("utf-8")
    ed25519_sig = ed25519_sig.split(" ")[1]

    rsa = keys / "ssh_host_rsa_key"
    if not rsa.exists():
        print("Creating rsa key")
        subprocess.check_call(["ssh-keygen", "-t", "rsa", "-f", f"{rsa}", "-N", ""])

    rsa_sig = subprocess.check_output(
        ["ssh-keygen", "-l", "-E", "SHA256", "-f", f"{rsa}.pub"]
    ).decode("utf-8")
    rsa_sig = rsa_sig.split(" ")[1]

    redis_password = generate_password()
    postgres_password = generate_password()
    minio_secret_key = generate_password()

    neo4j_password = getpass("neo4j password: ")
    neo4j_host = input("neo4j host: ")

    with open(deploy / "redis.conf", "w") as f:
        f.write(f"requirepass {redis_password}")

    with open(deploy / "redis.env", "w") as f:
        f.write(f"REDIS_PASSWORD={redis_password}\n")
        f.write("REDIS_HOST=redis:6379\n")
        f.write("REDIS_DB=0")

    with open(deploy / "server.env", "w") as f:
        f.write(
            SERVER_TEMPLATE.format(
                redis_password=redis_password,
                postgres_password=postgres_password,
                minio_secret_key=minio_secret_key,
                neo4j_host=neo4j_host,
                neo4j_password=neo4j_password,
            )
        )

    with open(deploy / "postgres.env", "w") as f:
        f.write("POSTGRES_USER=postgres\n")
        f.write(f"POSTGRES_PASSWORD={postgres_password}")

    with open(deploy / "tmate.env", "w") as f:
        f.write(
            PROXY_TEMPLATE.format(
                minio_secret_key=minio_secret_key,
                rsa_sig=rsa_sig,
                ed25519_sig=ed25519_sig,
            )
        )

    with open(deploy / "minio.env", "w") as f:
        f.write(MINIO_TEMPLATE.format(minio_secret_key=minio_secret_key))

    return 0


if __name__ == "__main__":
    exit(main())
