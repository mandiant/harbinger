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
    
    <div class="row q-gutter-sm">
      <q-btn color="secondary" icon="refresh" @click="store.LoadData()">Refresh</q-btn>
      <q-btn color="secondary" icon="download" @click="exportHashes()">Export</q-btn>
    </div>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Hashes" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="store.onRequest" selection="multiple" v-model:selected="selected">
      <template v-slot:top>
        <div class="col-2 q-table__title" v-if="selected.length === 0">Hashes</div>
        <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
            <bulk-label-actions :selected="selected" object-type="hash" @update="selected = []; store.LoadData()" />
            <q-btn dense icon="clear" @click="selected = []" flat>
              <q-tooltip>Clear Selection</q-tooltip>
            </q-btn>
            <div>{{ selected.length }} item(s) selected</div>
          </div>
        <q-space />
      </template>
      <template v-slot:header-selection="scope">
        <q-checkbox v-model="scope.selected" />
      </template>
      <template v-slot:body="props">
        <q-tr :props="props" class="cursor-pointer">
            <q-td>
            <q-checkbox v-model="props.selected" />
          </q-td>
          <q-td key="type" :props="props">
            {{ props.row.type }}
          </q-td>
          <q-td key="hashcat_id" :props="props">
            {{ props.row.hashcat_id }}
          </q-td>
          <q-td key="hash" :props="props"  @click="clipboard(props.row.hash)">
            {{ props.row.hash.substring(0, 100) }} ... {{ props.row.hash.substring(props.row.hash.length - 10) }}
          </q-td>
          <q-td key="time_created" :props="props">
            {{ props.row.time_created }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="hash" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar, copyToClipboard } from 'quasar';
import { Hash } from '../models';
import { useCounterStore } from 'src/stores/object-counters';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import { api } from 'src/boot/axios';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia';
import BulkLabelActions from 'src/components/BulkLabelActions.vue';

const useStore = defineTypedStore<Hash>('hashes');
const store = useStore();
const { loading, data, pagination } = storeToRefs(store);
store.Load();

const selected = ref([]);
const $q = useQuasar();

const counter_store = useCounterStore();

counter_store.clear('hashes');

const columns: QTableProps['columns'] = [
  { name: 'type', label: 'type', field: 'type', align: 'left', sortable: true },
  { name: 'hashcat_id', label: 'hashcat_id', field: 'hashcat_id', align: 'left', sortable: true },
  { name: 'hash', label: 'hash', field: 'hash', align: 'left', sortable: true },
  { name: 'time_created', label: 'time_created', field: 'time_created', align: 'left', sortable: true },
];

function clipboard(value: string) {
  copyToClipboard(value)
    .then(() => {
      // success!
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        message: 'Copied to clipboard!',
        position: 'top',
      });
    })
    .catch(() => {
      // fail
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Failed to copy to clipboard',
        icon: 'report_problem',
      });
    });
}

function exportHashes() {
  api.get('/hashes/export', { responseType: 'blob' }).then((response) => {
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'hashes.zip');
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
