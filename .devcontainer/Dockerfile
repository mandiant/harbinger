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

FROM trufflesecurity/trufflehog:3.73.0 as trufflehog

FROM ghcr.io/praetorian-inc/noseyparker:v0.17.0 as noseyparker

FROM python:3.11

ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME 

RUN apt-get update && apt-get install -y zip git wget unzip pandoc libmagic1 libimage-exiftool-perl python3-dev protobuf-compiler

RUN mkdir /opt/tools/

COPY harbinger/bofhound.txt /opt/tools/

RUN python -m venv /opt/tools/bofhound_venv && /opt/tools/bofhound_venv/bin/pip install -r /opt/tools/bofhound.txt --require-hashes --no-deps && rm /opt/tools/bofhound.txt

COPY --from=trufflehog /usr/bin/trufflehog /opt/tools/trufflehog

COPY --from=noseyparker /usr/local/bin/noseyparker /opt/tools/noseyparker

RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d

RUN groupadd --gid 1001 docker && usermod -aG docker $USERNAME

USER user:user
