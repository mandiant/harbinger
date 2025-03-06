<!--
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
-->

<template>
  <q-btn flat color='secondary' v-for="(ssh, index) in ssh_connections" v-bind:key="index" icon="open_in_new"
    target="_blank" :href="`ssh://${ssh.username}@${ssh.host}:${ssh.port}`">
    <template v-if="ssh.username.startsWith('ro-')">
      Read-only SSH
    </template>
    <template v-else>
      Interactive SSH
    </template>
  </q-btn>
  <q-input readonly v-model="output_str" filled type="textarea" autogrow dark :input-style="style" :bg-color="color"
    :loading="loading">
    <template v-slot:prepend>
      <q-icon color="green" name="wifi" v-if="connected">
        <q-tooltip v-if="connected">Event websocket is connected</q-tooltip>
      </q-icon>
      <q-btn flat v-else>
        <q-spinner-gears />
        <q-tooltip>Connecting to the websocket</q-tooltip>
      </q-btn>
    </template>
  </q-input>
</template>
<style>
.bg-powershell {
  background: #012456 !important;
}

.bg-bash {
  background: #2d2f38 !important;
}
</style>

<script setup lang="ts">
import { toRefs, ref, computed, onUnmounted } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import useLoadObject from 'src/load-object';
import { ProxyJob, ProxyJobOutput } from 'src/models';

const emit = defineEmits(['update']);

const $q = useQuasar();

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
});
const { id } = toRefs(props);
const { loading, object, loadObject } = useLoadObject<ProxyJob>(
  'proxy_jobs',
  id.value
);

loadObject()
const style = computed(() => {
  if (object.value !== null) {
    if (object.value.socks_server && object.value.socks_server.operating_system == 'linux') {
      return "font-family: 'Fira Code', monospace;";
    } else {
      return "font-family: 'Consolas';";
    }
  }
  return '';
});


const color = computed(() => {
  if (object.value !== null) {
    if (object.value.socks_server && object.value.socks_server.operating_system == 'linux') {
      return 'bash';
    } else {
      return 'powershell';
    }
  }
  return '';
});

const output = ref<Array<ProxyJobOutput>>([]);
const output_str = computed(() => {
  let result_str = '';
  if (object.value !== null) {
    if (object.value.socks_server && object.value.socks_server.operating_system == 'linux') {
      result_str = `[user:~]$ ${object.value.command} ${object.value.arguments}\n`;
    } else {
      result_str = `PS C:\\ > ${object.value.command} ${object.value.arguments}\n`;
    }
  }
  if (output.value) {
    output.value.forEach((element: ProxyJobOutput) => {
      result_str += element.output;
      result_str += '\n';
    });
  }

  return result_str;
});

function loadData() {
  api
    .get('/proxy_job_output/', { params: { job_id: id.value, size: 100 } })
    .then((response) => {
      output.value = response.data.items;
    })
    .catch(() => {
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Loading failed',
        icon: 'report_problem',
      });
    });
}
loadData();

const connection = ref<WebSocket>({} as WebSocket);

const connected = ref(false);

function CreateWebSocket() {
  let protocol = location.protocol.replace('http', 'ws');

  let ws_url = `${protocol}//${location.host}/proxy_jobs/${id.value}/output`;

  if (process.env.NODE_ENV === 'development') {
    ws_url = `${protocol}//localhost:8000/proxy_jobs/${id.value}/output`;
  }

  connection.value = new WebSocket(ws_url);

  connection.value.onmessage = function (event) {
    try {
      if (event.data) {
        let data = JSON.parse(event.data);
        output.value.push(data);
      }
      emit('update')
    } catch (e) { }
  };
  connection.value.onopen = function () {
    connected.value = true;
  };
  connection.value.onclose = function () {
    connected.value = false;
  };
}
// function reconnect() {
//   if (connected.value == false) {
//     CreateWebSocket();
//   }
// }

CreateWebSocket();

onUnmounted(() => {
  if (connection.value) {
    connection.value.close();
  }
});

interface SSH {
  port: number;
  host: string;
  username: string;
}
const ssh_connections = computed(() => {
  let result: Array<SSH> = []
  const regex = /ssh -p([0-9]*) ([a-z1-9A-Z\-]*)@([a-z1-9A-Z\-.]*)/
  output.value.forEach((element: ProxyJobOutput) => {
    const matches = regex.exec(element.output);
    if (matches) {
      let entry = {} as SSH
      entry.port = Number(matches[1])
      entry.username = matches[2]
      entry.host = matches[3]
      result.push(entry)
    }
  });
  return result;
})

</script>
