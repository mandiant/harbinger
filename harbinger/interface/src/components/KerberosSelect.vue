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
      v-model="selected"
      :option-label="(opt) => formatKerberos(opt)"
      :options="kerberos_entries"
      label="Kerberos"
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
import { Kerberos } from '../models';

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

const kerberos_entries = ref<Array<Kerberos>>([]);
const selected = ref(null);

function updateValue(event: Kerberos) {
  if (event !== null) {
    emit('update:modelValue', event.id);
  } else {
    emit('update:modelValue', null);
  }
}

function formatKerberos(obj: Kerberos) {
  if (obj === null) {
    return 'null';
  }

  return `${obj.client} - auth: ${obj.auth} - expires: ${obj.end}`;
}
function loadKerberos() {
  api
    .get('/kerberos/')
    .then((response) => {
      kerberos_entries.value = response.data.items;
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
loadKerberos();

function loadDefault() {
  if (modelValue.value) {
    api
      .get(`/kerberos/${modelValue.value}`)
      .then((response) => {
        selected.value = response.data;
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
    selected.value = null;
  }
});
</script>
