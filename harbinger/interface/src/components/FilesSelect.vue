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
      v-model="modelValue"
      :option-label="(opt) => formatFile(opt)"
      :options="files"
      label="File id"
      clearable
      @update:model-value="updateValue"
      @filter="filterFn"
      filled
      use-input
      multiple
    />
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { File } from '../models';

const $q = useQuasar();

const search = ref('');

const props = defineProps({
  modelValue: {
    type: Array<File>,
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

function updateValue(event: Array<string>) {
  if (event !== null) {
    emit('update:modelValue', event);
  } else {
    emit('update:modelValue', []);
  }
}

function formatFile(obj?: File) {
  if (obj?.filename) {
    return `${obj.filename}`;
  }
  return '';
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

function filterFn(val, update) {
  update(() => {
    search.value = val;
    loadFiles();
  });
}
</script>
