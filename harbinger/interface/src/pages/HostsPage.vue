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
    
    <q-btn color="secondary" icon="refresh" @click="hostStore.LoadData()">Refresh</q-btn>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Hosts" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="hostStore.onRequest">
      <template v-slot:top>
        <div class="col-2 q-table__title">Hosts</div>
        <q-space />
        <filter-view object-type="hosts" v-model="filters" v-on:updateFilters="hostStore.updateFilters" />
      </template>
      <template v-slot:body="props">
        <q-tr :props="props" class="cursor-pointer">
          <q-td key="id" :props="props" @click="Goto(props.row)">
            {{ props.row.id }}
          </q-td>
          <q-td key="name" :props="props" @click="Goto(props.row)">
            {{ props.row.name }}
          </q-td>
          <q-td key="objectid" :props="props" @click="Goto(props.row)">
            {{ props.row.objectid }}
          </q-td>
          <q-td key="domain" :props="props" @click="Goto(props.row)">
            {{ formatObject(props.row.domain_obj) }}
          </q-td>
          <q-td key="fqdn" :props="props" @click="Goto(props.row)">
            {{ props.row.fqdn }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="host" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">

import { useRouter } from 'vue-router';
import { Host, Domain } from '../models';
import { useCounterStore } from 'src/stores/object-counters';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const store = useCounterStore();

store.clear('hosts');
const $router = useRouter();

const useHosts = defineTypedStore<Host>('hosts');
const hostStore = useHosts();

const { loading, data, pagination, filters } = storeToRefs(hostStore);

function formatObject(obj?: Domain) {
  if (obj) {
    if (obj.long_name) {
      return obj.long_name;
    } else {
      return obj.short_name;
    }
  }
  return '';
}

hostStore.Load();
const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true },
  {
    name: 'objectid',
    label: 'objectid',
    field: 'objectid',
    align: 'left',
    sortable: true,
  },
  {
    name: 'domain',
    label: 'domain',
    field: 'domain',
    align: 'left',
    sortable: true,
  },
  { name: 'fqdn', label: 'fqdn', field: 'fqdn', align: 'left', sortable: true },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

function Goto(row: Host) {
  $router.push({ name: 'host', params: { id: row.id } });
}
</script>
