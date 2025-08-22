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
      <q-btn color="secondary" icon="add_circle" to="passwords/add">Add password</q-btn>
      <q-btn color="secondary" icon="refresh" @click="store.LoadData()">Refresh</q-btn>
    </div>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Passwords" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="store.onRequest" selection="multiple" v-model:selected="selected">
      <template v-slot:top>
        <div class="col-2 q-table__title" v-if="selected.length === 0">Passwords</div>
        <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
            <bulk-label-actions :selected="selected" object-type="password" @update="selected = []; store.LoadData()" />
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
          <q-td key="id" :props="props">
            {{ props.row.id }}
          </q-td>
          <q-td key="password" :props="props">
            {{ props.row.password }}
          </q-td>
          <q-td key="nt" :props="props">
            {{ props.row.nt }}
          </q-td>
          <q-td key="aes256_key" :props="props">
            {{ props.row.aes256_key }}
          </q-td>
          <q-td key="aes128_key" :props="props">
            {{ props.row.aes128_key }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="password" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">

import { ref } from 'vue';
import { Password } from '../models';
import { useCounterStore } from 'src/stores/object-counters';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia';
import BulkLabelActions from 'src/components/BulkLabelActions.vue';

const counter_store = useCounterStore();
const selected = ref([]);

counter_store.clear('passwords');

const useStore = defineTypedStore<Password>('passwords');
const store = useStore();

store.Load();

const { loading, data, pagination } = storeToRefs(store);

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  {
    name: 'password',
    label: 'password',
    field: 'password',
    align: 'left',
    sortable: true,
  },
  {
    name: 'nt',
    label: 'nt',
    field: 'nt',
    align: 'left',
    sortable: true,
  },
  {
    name: 'aes128_key',
    label: 'aes128_key',
    field: 'aes128_key',
    align: 'left',
    sortable: true,
  },
  {
    name: 'aes256_key',
    label: 'aes256_key',
    field: 'aes256_key',
    align: 'left',
    sortable: true,
  },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];
</script>
