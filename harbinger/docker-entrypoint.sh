#!/bin/bash
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


cat <<EOF > ~/.tmate.conf
set -g tmate-server-host $TMATE_SERVER
set -g tmate-server-port $TMATE_PORT
set -g tmate-server-rsa-fingerprint $RSA_SIG
set -g tmate-server-ed25519-fingerprint $ED25519_SIG
EOF

if [ -n "${PROXY_CONFIG}" ]; then
cat <<EOF > proxychains.conf
strict_chain
proxy_dns
remote_dns_subnet 224

tcp_read_time_out 100000000
tcp_connect_time_out 100000000

[ProxyList]
$PROXY_CONFIG
EOF
fi

eval $@
exit $?