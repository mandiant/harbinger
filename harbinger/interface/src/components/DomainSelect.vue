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
      v-model="selected_entry"
      :option-label="(opt) => formatObject(opt)"
      :options="options"
      label="Domain"
      clearable
      @update:model-value="updateValue"
      @filter="filterFn"
      filled
      use-input
      :error="!selected_entry && !optional"
      lazy-rules
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, toRefs } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { Domain } from '../models';

const $q = useQuasar();

const search = ref('');

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  optional: {
    type: Boolean,
    default: false,
  }
});

const { modelValue, optional } = toRefs(props);

const emit = defineEmits(['update:modelValue']);

const options = ref([]);
const selected_entry = ref(null);

function updateValue(event: Domain) {
  if (event !== null) {
    emit('update:modelValue', event.id);
  } else {
    emit('update:modelValue', null);
  }
}

function formatObject(obj?: Domain) {
  if (obj) {
    if (obj.long_name){
      return obj.long_name;
    } else {
      return obj.short_name;
    }
  }
  return '';
}

function loadObjects() {
  api
    .get('/domains/', { params: { search: search?.value } })
    .then((response) => {
      options.value = response.data.items;
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

loadObjects();

function loadDefault() {
  if (modelValue.value) {
    api
      .get(`/domains/${modelValue.value}`)
      .then((response) => {
        selected_entry.value = response.data;
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
    selected_entry.value = null;
  }
});

function filterFn(val: string, update: (a: () => void) => void) {
  update(() => {
    search.value = val;
    loadObjects();
  });
}
</script>
