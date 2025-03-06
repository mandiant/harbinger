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
  <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
    <q-input
      filled
      v-model="form.command"
      label="Command"
      hint="Command to execute"
      lazy-rules
      :rules="[(val) => (val && val.length > 0) || 'Please type something']"
    />

    <q-input
      filled
      v-model="form.arguments"
      label="Arguments for the command"
    />

    <socks-server-select v-model="form.socks_server_id"/>

    <q-select
      v-model="proxy"
      :option-label="(opt) => formatProxy(opt)"
      :options="proxies"
      label="Proxy"
      hint="optional"
      filled
    />

    <q-select
      v-model="credential"
      :option-label="(opt) => formatCredential(opt)"
      :options="credentials"
      label="Credential"
      hint="optional"
      filled
    />

    <files-select v-model="selected_files"/>
    <q-input filled v-model="form.env" label="env" hint="Environment flags, separate multiple with ','" />
    <q-toggle v-model="form.tmate" label="Use tmate" />
    <q-toggle v-model="form.asciinema" label="Use asciinema" />
    <q-toggle v-model="form.proxychains" label="Use proxychains" />

    <div>
      <q-btn
        label="Submit"
        type="submit"
        color="secondary"
        :loading="loading"
      />
      <q-btn
        label="Reset"
        type="reset"
        color="secondary"
        flat
        class="q-ml-sm"
      />
    </div>
  </q-form>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref, toRefs } from 'vue';
import { api } from 'boot/axios';
import { Proxy, Credential, File } from '../models';
import FilesSelect from './FilesSelect.vue';
import SocksServerSelect from './SocksServerSelect.vue';

const props = defineProps({
  modelValue: String,
  playbook_id: {
    type: String,
    default: '',
  },
});

const { playbook_id } = toRefs(props);
const emit = defineEmits(['update:modelValue']);

const $q = useQuasar();
const proxy = ref<Proxy | null>(null);
const credential = ref<Credential | null>(null);
const loading = ref(false);
const proxies = ref<Array<Proxy>>([]);
const credentials = ref<Array<Credential>>([]);
const selected_files = ref<Array<File>>([]);

interface Form {
  command: string;
  arguments: string;
  proxy_id?: string;
  credential_id?: string;
  socks_server_id: string;
  input_files: Array<string>;
  playbook_id?: string;
  asciinema: boolean;
  proxychains: boolean;
  tmate: boolean;
  env: string;
}

const form = ref<Form>({} as Form);

function onSubmit() {
  if (form.value.command != null) {
    loading.value = true;


    if (playbook_id.value) {
      form.value.playbook_id = playbook_id.value;
    }

    if (proxy.value !== null) {
      form.value.proxy_id = proxy.value.id;
    }

    if (credential.value !== null) {
      form.value.credential_id = credential.value.id;
    }

    form.value.input_files = selected_files.value.map(a => a.id),
    api
      .post('/proxy_jobs/', form.value)
      .then((response) => {
        $q.notify({
          color: 'green-4',
          textColor: 'white',
          icon: 'cloud_done',
          position: 'top',
          message: `Submitted, job_id: ${response.data.id}`,
        });
        emit('update:modelValue', response.data.id);
        loading.value = false;
      })
      .catch(() => {
        loading.value = false;
        $q.notify({
          color: 'negative',
          position: 'top',
          message: 'Loading failed',
          icon: 'report_problem',
        });
      });
  }
}

function formatProxy(obj: Proxy) {
  if (obj === null) {
    return 'null';
  }
  return `${obj.type}:${obj.host}:${obj.port} (${obj.status})`;
}

function formatCredential(obj: Credential) {
  if (obj === null) {
    return 'null';
  }

  let result = '';

  if (obj.domain) {
    result += obj.domain.long_name;
    result += '\\';
  }

  result += obj.username;

  return result;
}

function loadProxies() {
  api
    .get('/proxies/')
    .then((response) => {
      proxies.value = response.data.items;
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
loadProxies();

function loadCredentials() {
  api
    .get('/credentials/')
    .then((response) => {
      credentials.value = response.data.items;
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
loadCredentials();

function onReset() {
  form.value = {} as Form;
  credential.value = null;
  proxy.value = null;
  selected_files.value = [];
}
</script>
