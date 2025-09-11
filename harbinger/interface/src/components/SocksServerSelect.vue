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
  <div>
    <q-select
      v-model="socks_server"
      :option-label="(opt) => format(opt)"
      :options="socks_servers"
      label="Socks server"
      clearable
      @update:model-value="updateValue"
      filled
      :readonly="readonly"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, toRefs } from 'vue';
import { SocksServer } from '../models';
import { api } from 'src/boot/axios';
import { useQuasar } from 'quasar';

const $q = useQuasar();

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  values: {
    type: Array<string>,
    default: [],
  },
  operating_system: {
    type: String,
    default: '',
  },
  type: {
    type: String,
    default: '',
  }
});

const { modelValue, readonly } = toRefs(props);

const emit = defineEmits(['update:modelValue']);

const socks_servers = ref<Array<SocksServer>>([]);
const socks_server = ref<SocksServer>({} as SocksServer);

function updateValue(event: SocksServer) {
  if (event !== null) {
    emit('update:modelValue', event.id);
  } else {
    emit('update:modelValue', null);
  }
}

function format(obj: SocksServer) {
  if (obj.id) {
      return `[${obj.hostname}] os: ${obj.operating_system} type: ${obj.type} status: ${obj.status}`;
  }
  return '';
}

function loadCredentials() {
  api
    .get('/socks_servers')
    .then((response) => {
      socks_servers.value = response.data.items;
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

async function loadDefault() {
  if (modelValue.value) {
    api.get(`/socks_servers/${modelValue.value}`).then((response) => {
      socks_server.value = response.data;
    });
  }
}
loadDefault();

watch(modelValue, (old, new_model) => {
  if (old !== new_model) {
    loadDefault();
  }
  if (!modelValue.value) {
    socks_server.value = {} as SocksServer;
  }
});
</script>
