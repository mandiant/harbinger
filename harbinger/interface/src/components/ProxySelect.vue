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
    <q-select v-model="proxy" :option-label="(opt) => formatProxy(opt)" :options="proxies" label="Proxy" clearable
      @update:model-value="updateValue" filled :readonly="readonly" />
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs, watch } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { Proxy } from '../models';

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
});

const { modelValue, readonly } = toRefs(props);
const emit = defineEmits(['update:modelValue']);

const proxy = ref(null);
const proxies = ref<Array<Proxy>>([]);

function updateValue(event: Proxy) {
  if (event !== null) {
    emit('update:modelValue', event.id);
  } else {
    emit('update:modelValue', null);
  }
}

function formatProxy(obj: Proxy) {
  if (obj === null) {
    return 'null';
  }
  return `${obj.type}:${obj.host}:${obj.port} (${obj.status})`;
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

function loadDefault() {
  if (modelValue.value) {
    api
      .get(`/proxies/${modelValue.value}`)
      .then((response) => {
        proxy.value = response.data;
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
}
loadDefault();

watch(modelValue, (old, new_model) => {
  if (old !== new_model) {
    loadDefault();
  }
  if (!modelValue.value) {
    proxy.value = null;
  }
});
</script>
