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
  <div class="row q-gutter-sm">
    <q-btn color="secondary" icon="refresh" @click="store.LoadData()">Refresh</q-btn>
  </div>
  <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Socks Servers" :rows="data" row-key="id" :columns="columns" :loading="loading"
    v-model:pagination="pagination" @request="store.onRequest">
    <template v-slot:top> 
      <div class="row items-center" style="width: 100%;">
        <div class="col-auto q-table__title">Socks Servers</div>
      </div>
      <div class="row" style="width: 100%;">
        <filter-view object-type="socks/servers" v-model="filters" @updateFilters="store.updateFilters"
          class="full-width" />
      </div>
    </template>
    <template v-slot:body="props">
      <q-tr :props="props">
        <q-td key="id" :props="props">
          {{ props.row.id }}
        </q-td>
        <q-td key="type" :props="props">
          {{ props.row.type}}
        </q-td>
        <q-td key="name" :props="props">
          {{ props.row.name }}
        </q-td>
        <q-td key="hostname" :props="props">
          {{ props.row.hostname }}
        </q-td>
        <q-td key="operating_system" :props="props">
          {{ props.row.operating_system }}
        </q-td>
        <q-td key="status" :props="props">
          {{ props.row.status }}
        </q-td>
        <q-td key="labels" :props="props">
          <labels-list object-type="socks_server" :object-id="String(props.row.id)" v-model="props.row.labels" />
        </q-td>
      </q-tr>
    </template>
  </q-table>
</template>

<script setup lang="ts">
import { SocksServer } from '../models';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { useCounterStore } from 'src/stores/object-counters';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'
const counter_store = useCounterStore();

counter_store.clear('socks_servers');

const useStore = defineTypedStore<SocksServer>('socks/servers');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  { name: 'type', label: 'type', field: 'type', align: 'left', sortable: true },
  {
    name: 'hostname',
    label: 'hostname',
    field: 'hostname',
    align: 'left',
    sortable: true,
  },
  {
    name: 'operating_system',
    label: 'operating_system',
    field: 'operating_system',
    align: 'left',
    sortable: true,
  },
  {
    name: 'status',
    label: 'status',
    field: 'status',
    align: 'left',
    sortable: true,
  },
  {
    name: 'labels',
    label: 'labels',
    field: 'labels',
    align: 'left',
    sortable: true,
  },
];

</script>
