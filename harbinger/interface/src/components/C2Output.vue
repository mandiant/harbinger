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
  <q-card-section class="row q-gutter-sm">
    <div class="text-h6">Output</div>
    {{  task_id }}
    <q-btn color="secondary" icon="download" @click="exportOutput()">Export</q-btn>
    <q-btn color="secondary" icon="refresh" @click="store.LoadData">Refresh</q-btn>
  </q-card-section>
  <q-card-section>
    <q-timeline dense color="secondary">
      <filter-view object-type="c2_output" v-model="filters" v-on:updateFilters="store.updateFilters" />
      <q-timeline-entry v-for="entry in data" v-bind:key="entry.id">
        <template v-slot:title>
          <labels-list object-type="c2_task_output" :object-id="String(entry.id)" v-model="entry.labels" />
        </template>
        <template v-slot:subtitle>
          {{ entry.timestamp }}
        </template>
        <q-input v-model="entry.response_text" readonly autogrow v-if="entry.response_text" />
      </q-timeline-entry>
      <q-inner-loading :showing="loading">
        <q-spinner-gears size="50px" color="secondary" />
      </q-inner-loading>
    </q-timeline>
  </q-card-section>
  <q-card-actions class="column items-center" v-if="pages > 1">
    <q-pagination v-model="current" direction-links :max="pages" flat color="grey" active-color="primary" />
  </q-card-actions>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { toRefs, ref, computed, watch } from 'vue';
import { C2Output } from '../models';
import { api } from 'src/boot/axios';
import FilterView from '../components/FilterView.vue';
import LabelsList from './LabelsList.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const $q = useQuasar();

const props = defineProps({
  implant_id: {
    type: String,
    default: '',
  },
  task_id: {
    type: String,
    default: '',
  },
  c2_job_id: {
    type: String,
    default: '',
  },
});

const useStore = defineTypedStore<C2Output>('c2_output');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);

const current = ref(1);

const { implant_id, task_id, c2_job_id } = toRefs(props);

if (implant_id.value) {
  store.AddFilter({ c2_implant_id: implant_id.value });
} else {
  store.RemoveFilter('c2_implant_id')
}
if (task_id.value) {
  store.AddFilter({ c2_task_id: task_id.value })
} else {
  store.RemoveFilter('c2_task_id')
}
if (c2_job_id.value) {
  store.AddFilter({ c2_job_id: c2_job_id.value })
} else {
  store.RemoveFilter('c2_job_id')
}

store.LoadData();


watch(current, (old_value, new_value) => {
  if (old_value !== new_value) {
    pagination.value.page = current.value;
    store.LoadData();
  }
});

const pages = computed(() =>
  Math.ceil(pagination.value.rowsNumber / pagination.value.rowsPerPage)
);


function exportOutput() {
  api.get('/c2_output/export', { params: { ...store.filters }, responseType: 'blob' }).then((response) => {
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'output.txt');
    document.body.appendChild(link);
    link.click();
    $q.notify({
      color: 'green-4',
      textColor: 'white',
      icon: 'cloud_done',
      position: 'top',
      message: 'Exported hashes',
    });
  }).catch(() => {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: 'Error exporting hashes',
      icon: 'report_problem',
    });
  });
}
</script>
