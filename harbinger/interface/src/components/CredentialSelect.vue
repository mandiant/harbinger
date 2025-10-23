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
      v-model="credential"
      :option-label="(opt) => formatCredential(opt)"
      :options="credentials"
      label="Credential"
      clearable
      @update:model-value="updateValue"
      filled
      :readonly="readonly"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs, watch } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { Credential } from '../models';

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

const credentials = ref<Array<Credential>>([]);
const credential = ref(null);

function updateValue(event: Credential) {
  if (event !== null) {
    emit('update:modelValue', event.id);
  } else {
    emit('update:modelValue', null);
  }
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

  if (obj.username) {
    result += obj.username;
  }

  if (obj.password){
    if (obj.password.nt){
      result += ` nt: ${obj.password.nt}`;
    } else if (obj.password.password){
      result += ` ${obj.password.password}`;
    }
  }
  if (obj.kerberos) {
    result += ` client: ${obj.kerberos.client} server: ${obj.kerberos.server}`
  }
  return result;
}
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

function loadDefault() {
  if (modelValue.value) {
    api
      .get(`/credentials/${modelValue.value}`)
      .then((response) => {
        credential.value = response.data;
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
    credential.value = null;
  }
});
</script>
