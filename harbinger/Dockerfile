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

# Build harbinger
FROM python:3.11 as build_harbinger

COPY base-tooling-requirements.txt base-tooling-requirements.txt

RUN pip install -r base-tooling-requirements.txt --require-hashes

WORKDIR /project

COPY . /project

RUN python -m build

# Build the interface
FROM node:20 as quasar_build

COPY interface /interface

RUN mkdir /server

WORKDIR /interface

RUN npm i -g @quasar/cli

RUN npm install

RUN quasar build

FROM trufflesecurity/trufflehog:3.73.0 as trufflehog

FROM ghcr.io/praetorian-inc/noseyparker:v0.17.0 as noseyparker

# base image
FROM python:3.11

RUN apt-get update && apt-get install -y zip git wget unzip pandoc libmagic1 libimage-exiftool-perl jq nano

COPY requirements.txt requirements.txt

#RUN GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=1 pip install -r requirements.txt --require-hashes --no-deps --no-binary=grpcio --use-feature=no-binary-enable-wheel-cache
RUN pip install -r requirements.txt --require-hashes --no-deps

RUN mkdir /opt/tools/

COPY bofhound.txt /opt/tools/

RUN python -m venv /opt/tools/bofhound_venv && /opt/tools/bofhound_venv/bin/pip install -r /opt/tools/bofhound.txt --require-hashes --no-deps && rm /opt/tools/bofhound.txt

RUN wget https://github.com/asciinema/agg/releases/download/v1.4.3/agg-x86_64-unknown-linux-gnu -O /usr/bin/agg && chmod +x /usr/bin/agg

RUN wget -qO adexplorersnapshot.tar.gz https://github.com/t94j0/adexplorersnapshot-rs/releases/download/v0.0.2/adexplorersnapshot-v0.0.2-x86_64-unknown-linux-gnu.tar.gz && \
    echo "9b818dc869f9353bde9a19ad1d5c19877236ec33c915d961062d60e3cd395d65  adexplorersnapshot.tar.gz" | sha256sum -c - && \
    tar xvf adexplorersnapshot.tar.gz -C /usr/local/bin --strip-components=1 adexplorersnapshot-v0.0.2-x86_64-unknown-linux-gnu/convertsnapshot && \
    chmod +x /usr/local/bin/convertsnapshot && \
    rm adexplorersnapshot.tar.gz

COPY --from=trufflehog /usr/bin/trufflehog /opt/tools/trufflehog

COPY --from=noseyparker /usr/local/bin/noseyparker /opt/tools/noseyparker

COPY --from=build_harbinger /project/dist/harbinger-0.1.0-py3-none-any.whl /opt/

RUN pip install /opt/harbinger-0.1.0-py3-none-any.whl --no-deps --no-index

WORKDIR /server

COPY --from=quasar_build server/dist /server/dist

RUN cp dist/*.png dist/assets/

EXPOSE 8000/tcp

ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME

RUN mkdir /workdir

RUN chown $USER_UID:$USER_GID /workdir

RUN chown $USER_UID:$USER_GID /server

VOLUME /workdir

USER user:user
