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
  <q-card flat>
    <q-card-section>
      <q-inner-loading :showing="loading">
        <q-spinner-gears size="50px" color="secondary" />
      </q-inner-loading>
      <q-form class="q-gutter-md">
        <q-input filled v-model="job.command" label="command" :readonly="readonly || job.status !== 'created'" dense />
        <q-input filled v-model="job.arguments" label="arguments" :readonly="readonly || job.status !== 'created'" dense
          multiline autogrow />
        <q-input filled v-model="job.status" label="status" readonly dense v-if="extra" />
        <q-input filled v-model="job.message" label="message" readonly dense autogrow v-if="extra" />
        <c2-implant-select v-model="job.c2_implant_id" v-if="job.c2_implant_id"
          :readonly="readonly || job.status !== 'created'" />
        <q-select filled v-model="job.input_files" use-chips stack-label emit-value multiple label="Input Files"
          :readonly="readonly || job.status !== 'created'" :options="file_store.files" option-label="filename" />
      </q-form>
    </q-card-section>
    <q-card-section>
      <labels-list object-type="c2_job" :object-id="String(job.id)" v-model="job.labels" />
    </q-card-section>
    <q-card-actions v-show="!readonly && job.status === 'created'">
      <q-btn color="secondary" icon="save" flat @click="save">Save</q-btn>
      <q-btn color="secondary" icon="delete" flat @click="emit('delete')">
        Delete
      </q-btn>
      <q-btn color="secondary" icon="content_copy" flat @click="emit('clone')">
        Clone
      </q-btn>
    </q-card-actions>
    <q-card-actions v-if="extra">
      <q-btn color="secondary" icon="play_arrow" flat @click="start"
        v-show="!readonly && job.status === 'created' && !(job.playbook_id)">
        Start</q-btn>
    </q-card-actions>
    <q-card-section v-if="job.status !== 'created' && !dialog">
      <c2-output :c2_job_id="job_id" />
    </q-card-section>
    <q-card-section v-if="dialog">
      <q-btn flat icon="output" label="Output" @click="showDialog = true" />
    </q-card-section>
    <q-dialog v-model="showDialog">
      <q-card style="min-width: 80vw; max-width: 80vw;">
        <q-card-section>
          <c2-output :c2_job_id="job_id" />
        </q-card-section>
        <q-card-actions>
          <q-btn color="primary" label="OK" @click="showDialog = false" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-card>
</template>

<script setup lang="ts">
import { ref, toRefs, watch } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { C2Job } from '../models';
import C2ImplantSelect from './C2ImplantSelect.vue';
import C2Output from './C2Output.vue';
import { useFileStore } from 'src/stores/files';
import LabelsList from 'src/components/LabelsList.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'


const store = defineTypedStore<C2Job>('c2_jobs')();
const file_store = useFileStore();

const $q = useQuasar();

const props = defineProps({
  job_id: {
    type: String,
    required: true,
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  extra: {
    type: Boolean,
    default: false,
  },
  dialog: {
    type: Boolean,
    default: false,
  }
});
const emit = defineEmits(['delete', 'clone']);

const showDialog = ref(false);

const { job_id, extra, readonly, dialog } = toRefs(props);

const job = ref<C2Job>({ c2_implant_id: '', labels: [] } as C2Job);

store.updateCache(job_id.value);

const { cache } = storeToRefs(store);

const loading = ref(true);

watch(cache, () => {
  const test = cache.value[job_id.value]
  if (test){
    job.value = test
  }
}, { deep: true })


store.loadById(job_id.value).then((item => {
  loading.value = false;
  job.value = item
}));

function start() {
  api
    .post(`/c2_jobs/${job_id.value}/start`)
    .then(() => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: 'Started',
        position: 'top',
      });
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Starting failed',
        icon: 'report_problem',
      });
    });
}

function save() {
  loading.value = true;

  const files = job.value.input_files

  job.value.input_files = []
  files.forEach((element) => {
    job.value.input_files.push(element.id)
  })

  api
    .put(`/c2_jobs/${job_id.value}`, job.value)
    .then((response) => {
      job.value = response.data;
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: 'Updated',
        position: 'top',
      });
    })
    .catch((error) => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: `Updating failed: ${error.response.data}`,
        icon: 'report_problem',
      });
    });
}

</script>
