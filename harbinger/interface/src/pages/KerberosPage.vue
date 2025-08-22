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
    </div>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Kerberos Tickets" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="store.onRequest" selection="multiple" v-model:selected="selected">
      <template v-slot:top>
        <div class="col-2 q-table__title" v-if="selected.length === 0">Kerberos Tickets</div>
        <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
            <bulk-label-actions :selected="selected" object-type="kerberos" @update="selected = []; store.LoadData()" />
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
        <q-tr :props="props">
            <q-td>
            <q-checkbox v-model="props.selected" />
          </q-td>
          <q-td key="client" :props="props">
            {{ props.row.client }}
          </q-td>
          <q-td key="server" :props="props">
            {{ props.row.server }}
          </q-td>
          <q-td key="key" :props="props">
            <q-btn v-if="props.row.key" @click="clipboard(props.row.key)" color="secondary" icon="content_copy">
              <q-tooltip>Copy to clipboard</q-tooltip>
            </q-btn>
          </q-td>
          <q-td key="keytype" :props="props">
            {{ props.row.keytype }}
          </q-td>
          <q-td key="auth" :props="props">
            {{ props.row.auth }}
          </q-td>
          <q-td key="start" :props="props">
            {{ props.row.start }}
          </q-td>
          <q-td key="end" :props="props">
            {{ props.row.end }}
          </q-td>
          <q-td key="renew" :props="props">
            {{ props.row.renew }}
          </q-td>
          <q-td key="ccache" :props="props">
            <q-btn v-if="props.row.ccache" @click="clipboard(props.row.ccache)" color="secondary" icon="content_copy">
              <q-tooltip>Copy to clipboard</q-tooltip>
            </q-btn>
          </q-td>
          <q-td key="kirbi" :props="props">
            <q-btn v-if="props.row.kirbi" @click="clipboard(props.row.kirbi)" color="secondary" icon="content_copy">
              <q-tooltip>Copy to clipboard</q-tooltip>
            </q-btn>
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="kerberos" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar, copyToClipboard } from 'quasar';
import { Kerberos } from '../models';
import { useCounterStore } from 'src/stores/object-counters';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia';
import BulkLabelActions from 'src/components/BulkLabelActions.vue';

const useStore = defineTypedStore<Kerberos>('kerberos');
const store = useStore();
const { loading, data, pagination } = storeToRefs(store);
store.Load();

const selected = ref([]);
const $q = useQuasar();

const counter_store = useCounterStore();

counter_store.clear('kerberos');

const columns: QTableProps['columns'] = [
  { name: 'client', label: 'client', field: 'client', align: 'left', sortable: true },
  { name: 'server', label: 'server', field: 'server', align: 'left', sortable: true },
  { name: 'key', label: 'key', field: 'key', align: 'left', sortable: true },
  { name: 'keytype', label: 'auth', field: 'auth', align: 'left', sortable: true },
  { name: 'auth', label: 'auth', field: 'auth', align: 'left', sortable: true },
  { name: 'start', label: 'start', field: 'start', align: 'left', sortable: true },
  { name: 'end', label: 'end', field: 'end', align: 'left', sortable: true },
  { name: 'renew', label: 'renew', field: 'renew', align: 'left', sortable: true },
  { name: 'ccache', label: 'ccache', field: 'ccache', align: 'left', sortable: true },
  { name: 'kirbi', label: 'kirbi', field: 'kirbi', align: 'left', sortable: true },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
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

</script>
