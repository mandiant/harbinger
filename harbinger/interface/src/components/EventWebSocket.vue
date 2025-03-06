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
  <q-icon color="green" name="wifi" v-if="store.connected">
    <q-tooltip v-if="store.connected">Event websocket is connected</q-tooltip>
  </q-icon>
  <q-btn flat v-else>
    <q-spinner-gears />
    <q-tooltip>Connecting to the websocket</q-tooltip>
  </q-btn>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue';
import { useCounterStore } from 'src/stores/object-counters';
import { useLabelStore } from 'src/stores/labels';
import { useFileStore } from 'src/stores/files';
import { useMythicImplantStore } from 'src/stores/mythic_implants'
import { useMetaStore } from 'src/stores/meta';
import { useProgressStore } from 'src/stores/progress'
import { 
  Event, C2Implant, C2Task, C2Job, C2Server, Domain,
  Password, Credential, Proxy, ProxyJob, Component,
  File, Host, Label, Kerberos, SituationalAwareness,
  Share, Hash, CertificateTemplate, CertificateAuthority, Issue, Action,
  C2ServerType, Progress, Chain, Highlight, Suggestion, Checklist, Objective
} from '../models';
import { debounce } from 'quasar';
import { useMeta } from 'quasar'
import { defineTypedStore } from 'src/stores/datastore';
import { Store } from 'pinia';


const connection = ref<WebSocket>({} as WebSocket);

const store = useCounterStore();

const label_store = useLabelStore();

const file_store = useFileStore();

const c2_implant_store = useMythicImplantStore();

const progress_store = useProgressStore();

const storeMap = new Map<string, Store>();
storeMap.set('c2_implant', defineTypedStore<C2Implant>('c2/implants')());
storeMap.set('c2_task', defineTypedStore<C2Task>('c2/tasks')());
storeMap.set('c2_job', defineTypedStore<C2Job>('c2/jobs')());
storeMap.set('c2_server', defineTypedStore<C2Server>('c2/servers')());
storeMap.set('domain', defineTypedStore<Domain>('domains')());
storeMap.set('password', defineTypedStore<Password>('passwords')());
storeMap.set('credential', defineTypedStore<Credential>('credentials')());
storeMap.set('proxy', defineTypedStore<Proxy>('proxies')());
storeMap.set('proxy_job', defineTypedStore<ProxyJob>('proxy_jobs')());
storeMap.set('component', defineTypedStore<Component>('components')());
storeMap.set('file', defineTypedStore<File>('files')());
storeMap.set('host', defineTypedStore<Host>('hosts')());
storeMap.set('label', defineTypedStore<Label>('labels')());
storeMap.set('kerberos', defineTypedStore<Kerberos>('kerberos')());
storeMap.set('situational_awareness', defineTypedStore<SituationalAwareness>('situational_awareness')());
storeMap.set('share', defineTypedStore<Share>('shares')());
storeMap.set('hash', defineTypedStore<Hash>('hashes')());
storeMap.set('certificate_template', defineTypedStore<CertificateTemplate>('certificate_templates')());
storeMap.set('certificate_authority', defineTypedStore<CertificateAuthority>('certificate_authoritiess')());
storeMap.set('issue', defineTypedStore<Issue>('issues')());
storeMap.set('action', defineTypedStore<Action>('actions')());
storeMap.set('c2_server_type', defineTypedStore<C2ServerType>('c2_server_types')());
storeMap.set('progress', defineTypedStore<Progress>('progress_bars')());
storeMap.set('playbook', defineTypedStore<Chain>('playbooks')());
storeMap.set('highlight', defineTypedStore<Highlight>('highlights')());
storeMap.set('suggestion', defineTypedStore<Suggestion>('suggestions')());
storeMap.set('checklist', defineTypedStore<Checklist>('checklists')());
storeMap.set('objective', defineTypedStore<Objective>('objectives')());

const retry = ref(true);

function CreateWebSocket() {
  let protocol = location.protocol.replace('http', 'ws');

  let ws_url = `${protocol}//${location.host}/events`;

  if (process.env.NODE_ENV === 'development') {
    ws_url = `${protocol}//localhost:8000/events`;
  }

  connection.value = new WebSocket(ws_url);

  connection.value.onmessage = function (event) {
    try {
      let data: Event = JSON.parse(event.data); 
      if (storeMap.has(data.event)) {
        const store = storeMap.get(data.event);
        if (store && data.event !== 'progress') {
          store.updateCache(data.id);
        }
      }
      if (data.name == 'new') {
        store.incrementObject(data.event);
        if (data.event === 'label') {
          label_store.loadLabels()
        } else if (data.event === 'file') {
          file_store.loadFiles()
        } else if (data.event === 'c2_implant') {
          c2_implant_store.ReLoadAliveImplants()
        } else if (data.event === 'labeled_item') {
          c2_implant_store.ReLoadAliveImplants()
        }
      } else if (data.name === 'deleted') {
        if (data.event === 'labeled_item') {
          c2_implant_store.ReLoadAliveImplants()
        }
      }
      if (data.event === 'progress') {
        if (data.name === 'update') {
          progress_store.UpdateProgress(data.progress.id, data.progress.current, data.progress.percentage)
        } else if (data.name === 'new') {
          progress_store.AddProgress(data.progress)
        } else if (data.name === 'deleted') {
          progress_store.DeleteProgress(data.progress.id)
        }
      }
    } catch (e) { }
  };
  connection.value.onopen = function () {
    store.setConnected();
    label_store.loadLabels()
    file_store.loadFiles()
    file_store.loadFileTypes()
    c2_implant_store.ReLoadAliveImplants()
    progress_store.loadProgressBars()
  };
  connection.value.onclose = function () {
    store.setDisconnected();
    reconnect();
  };
}

const reconnect = debounce(function () {
  if (!store.isConnected && retry.value) {
    CreateWebSocket();
  }
}, 500);


CreateWebSocket();

onUnmounted(() => {
  retry.value = false;
  if (connection.value) {
    connection.value.close();
  }
});

const meta = useMetaStore();

useMeta(() => {
  return {
    title: meta.title
  }
})

</script>
