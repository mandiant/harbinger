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
      v-model="selected_file"
      :option-label="(opt) => formatFile(opt)"
      :options="files"
      label="File id"
      clearable
      @update:model-value="updateValue"
      @filter="filterFn"
      filled
      use-input
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, toRefs } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { File } from '../models';

const $q = useQuasar();

const search = ref('');

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  fileType: {
    type: String,
    default: '',
  }
});

const { modelValue, fileType } = toRefs(props);

const emit = defineEmits(['update:modelValue']);

const files = ref([]);
const selected_file = ref(null);

function updateValue(event: File) {
  if (event !== null) {
    emit('update:modelValue', event.id);
  } else {
    emit('update:modelValue', null);
  }
}

function formatFile(obj?: File) {
  if (obj) {
    return `${obj.filename}`;
  }
  return null;
}

function loadFiles() {
  var params = {}
  if (search?.value) {
    params = { search: search?.value }
  }
  if (fileType?.value) {
    params = { ...params, filetype: fileType?.value }
  }
  api
    .get('/files/', { params: params })
    .then((response) => {
      files.value = response.data.items;
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

loadFiles();

function loadDefault() {
  if (modelValue.value) {
    api
      .get(`/files/${modelValue.value}`)
      .then((response) => {
        selected_file.value = response.data;
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
    selected_file.value = null;
  }
});

function filterFn(val, update) {
  update(() => {
    search.value = val;
    loadFiles();
  });
}
</script>
