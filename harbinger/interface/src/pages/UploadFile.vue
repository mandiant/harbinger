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
  <q-page padding>
    <bread-crumb />
    <q-card flat class="q-pa-md">
      <q-card-section>
        <h5>Upload a file</h5>
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <q-file v-model="model" label="Upload file"></q-file>
          <q-select use-input v-model="file_type" :options="options" @filter="filterFn"
            label="Filetype"></q-select>
          <q-btn label="Submit" type="submit" color="secondary" :loading="loading" />
          <q-btn label="Reset" type="reset" color="secondary" flat class="q-ml-sm" />
        </q-form>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'src/boot/axios';
import { useRouter } from 'vue-router';
import BreadCrumb from '../components/BreadCrumb.vue';
import { useFileStore } from 'src/stores/files';

const $q = useQuasar();

const $router = useRouter();

const file_store = useFileStore();

const options = ref(file_store.fileTypes);

const model = ref(null);
const file_type = ref('');
const loading = ref(false);

function onSubmit() {
  if (model.value != null) {
    let formdata = new FormData();
    formdata.append('file', model.value);
    loading.value = true;
    api
      .post('/upload_file/', formdata, {
        headers: { 'Content-Type': 'multipart/form-data' },
        params: { file_type: file_type.value },
      })
      .then(() => {
        loading.value = false;
        $q.notify({
          color: 'green-4',
          textColor: 'white',
          icon: 'cloud_done',
          message: 'uploaded!',
          position: 'top',
        });
        $router.push({ name: 'files' });
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

function onReset() {
  model.value = null;
  file_type.value = '';
}

function filterFn(val: string, update: (a: () => void) => void) {
  if (val === '') {
    update(() => {
      options.value = file_store.fileTypes
    })
    return
  }

  update(() => {
    const needle = val.toLowerCase()
    options.value = file_store.fileTypes.filter(v => v.toLowerCase().indexOf(needle) > -1)
  })
}
</script>
