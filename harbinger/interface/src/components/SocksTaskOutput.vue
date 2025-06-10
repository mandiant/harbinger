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
  <div class="q-pa-md">
    <q-card class="q-mt-md">
      <q-tabs
        v-model="currentTab"
        dense
        class="text-grey"
        active-color="primary"
        indicator-color="primary"
        align="justify"
        narrow-indicator
      >
        <q-tab name="output" label="Output" />
        <q-tab
          name="readonly_terminal"
          label="Read-only Terminal"
          :disable="!hasReadOnlySsh"
        />
        <q-tab
          name="interactive_terminal"
          label="Read/Write Terminal"
          :disable="!hasInteractiveSsh"
        />
      </q-tabs>

      <q-separator />

      <q-tab-panels v-model="currentTab" animated>
        <q-tab-panel name="output">
          <q-input readonly v-model="output_str" filled type="textarea" autogrow dark
            :input-style="style" :bg-color="color" :loading="loading">
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
        </q-tab-panel>

        <q-tab-panel name="readonly_terminal">
          <div v-if="hasReadOnlySsh">
            <TerminalComponent
              :initial-job-id="id"
              initial-session-type="readonly"
              :auto-connect="currentTab === 'readonly_terminal'"
            />
          </div>
          <div v-else>
            <q-banner dense class="bg-warning text-white">
              No read-only SSH connection details found in the output yet.
            </q-banner>
          </div>
        </q-tab-panel>

        <q-tab-panel name="interactive_terminal">
          <div v-if="hasInteractiveSsh">
            <TerminalComponent
              :initial-job-id="id"
              initial-session-type="interactive"
              :auto-connect="currentTab === 'interactive_terminal'"
            />
          </div>
          <div v-else>
            <q-banner dense class="bg-warning text-white">
              No interactive SSH connection details found in the output yet.
            </q-banner>
          </div>
        </q-tab-panel>
      </q-tab-panels>
    </q-card>
  </div>
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
import { toRefs, ref, computed, onUnmounted, watch } from 'vue';
import { api } from 'boot/axios';
import { useQuasar, QTabs, QTab, QTabPanel, QTabPanels, QBanner } from 'quasar'; // Import Quasar components used in template
import useLoadObject from 'src/load-object';
import { ProxyJob, ProxyJobOutput } from 'src/models';
import TerminalComponent from './TerminalComponent.vue'; // Import the Terminal component

const emit = defineEmits(['update']);
const $q = useQuasar();

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
});
const { id } = toRefs(props); // `id` is a Ref<string> now

const { loading, object, loadObject } = useLoadObject<ProxyJob>(
  'proxy_jobs',
  id.value // Use the ref's value here
);

// Initial load of the proxy job details
loadObject();

const style = computed(() => {
  if (object.value !== null && object.value.socks_server) {
    if (object.value.socks_server.operating_system === 'linux') {
      return "font-family: 'Fira Code', monospace;";
    } else {
      return "font-family: 'Consolas';";
    }
  }
  return '';
});

const color = computed(() => {
  if (object.value !== null && object.value.socks_server) {
    if (object.value.socks_server.operating_system === 'linux') {
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
    if (object.value.socks_server && object.value.socks_server.operating_system === 'linux') {
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

const connection = ref<WebSocket | null>(null); // Initialize as null
const connected = ref(false);
const currentTab = ref('output'); // Reactive variable to control active tab

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
  let result: Array<SSH> = [];
  // More robust regex to handle variations and ensure full capture
  const regex = /ssh -p(\d+)\s+([a-zA-Z0-9_-]+)@\"?([a-zA-Z0-9_.-]+)\"?/g; // Added /g for global search
  
  // Iterate over output lines to find all potential SSH connections
  output.value.forEach((element: ProxyJobOutput) => {
    let match;
    // Use regex.exec in a loop to find all matches in the output string
    // reset lastIndex for new element iteration if regex is global
    regex.lastIndex = 0; // Important when using /g flag in regex.exec within a loop
    while ((match = regex.exec(element.output)) !== null) {
      // This is important to avoid infinite loops with zero-width matches
      if (match.index === regex.lastIndex) {
        regex.lastIndex++;
      }
      let entry: SSH = {
        port: Number(match[1]),
        username: match[2],
        host: match[3]
      };
      // Prevent duplicate entries, especially if the same SSH string appears multiple times
      if (!result.some(e => e.host === entry.host && e.port === entry.port && e.username === entry.username)) {
        result.push(entry);
      }
    }
  });
  return result;
});

const hasReadOnlySsh = computed(() => {
  return ssh_connections.value.some(ssh => ssh.username.startsWith('ro-'));
});

const hasInteractiveSsh = computed(() => {
  // An interactive SSH connection is one that does NOT start with 'ro-'
  return ssh_connections.value.some(ssh => !ssh.username.startsWith('ro-'));
});

// Watch the output to re-evaluate SSH connections and potentially enable tabs
watch(output, () => {
  // The computed properties `hasReadOnlySsh` and `hasInteractiveSsh` will automatically
  // re-evaluate when `output.value` changes, and their values will update the tab `disable` props.
  // No explicit action needed here beyond the computed properties.
}, { deep: true }); // Watch deeply for changes within the output array items

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
        message: 'Loading initial output failed',
        icon: 'report_problem',
      });
    });
}
// Call loadData() again to ensure initial output is fetched
loadData();
</script>
