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
    <div class="row q-gutter-sm">
      <q-btn color="secondary" icon="add_circle" to="proxies/add">Add a proxy</q-btn>
      <q-btn color="secondary" icon="refresh" @click="store.LoadData()">Refresh</q-btn>
    </div>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Socks Proxies" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="store.onRequest" :visible-columns="visible">
      <template v-slot:top> 
        <div class="row items-center" style="width: 100%;">
          <div class="col-auto q-table__title">Socks Proxies</div>
          <q-space />
          <q-select v-model="visible" multiple borderless dense options-dense :display-value="$q.lang.table.columns"
            emit-value map-options :options="columns" option-value="name" style="min-width: 150px">
            <template v-slot:option="{ itemProps, opt, selected, toggleOption }">
              <q-item v-bind="itemProps">
                <q-item-section>
                  <q-item-label :class="$q.dark.isActive ? 'text-white' : 'text-black'">{{ opt.label }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-toggle :model-value="selected" @update:model-value="toggleOption(opt)" />
                </q-item-section>
              </q-item>
            </template>
          </q-select>
        </div>
        <div class="row" style="width: 100%;">
          <filter-view object-type="proxies" v-model="filters" @updateFilters="store.updateFilters"
            class="full-width" />
        </div>
      </template>
      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td key="id" :props="props">
            {{ props.row.id }}
          </q-td>
          <q-td key="host" :props="props">
            {{ props.row.host }}
          </q-td>
          <q-td key="port" :props="props">
            {{ props.row.port }}
          </q-td>
          <q-td key="type" :props="props">
            {{ props.row.type }}
          </q-td>
          <q-td key="status" :props="props">
            {{ props.row.status }}
          </q-td>
          <q-td key="note" :props="props">
            {{ props.row.note }}
          </q-td>
          <q-td key="remote_hostname" :props="props">
            {{ props.row.remote_hostname }}
          </q-td>
          <q-td key="username" :props="props">
            {{ props.row.username }}
          </q-td>
          <q-td key="password" :props="props">
            {{ Truncate(props.row.password) }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="proxy" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import BreadCrumb from '../components/BreadCrumb.vue';
import { Proxy } from '../models';
import { useCounterStore } from 'src/stores/object-counters';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import { Truncate } from 'src/truncate';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'
import FilterView from '../components/FilterView.vue';
import { ref } from 'vue';

const counter_store = useCounterStore();

counter_store.clear('proxies');

const visible = ref(['host', 'port', 'type', 'status', 'remote_hostname'])

const useStore = defineTypedStore<Proxy>('proxies');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  { name: 'host', label: 'host', field: 'host', align: 'left', sortable: true },
  { name: 'port', label: 'port', field: 'port', align: 'left', sortable: true },
  { name: 'type', label: 'type', field: 'type', align: 'left', sortable: true },
  {
    name: 'status',
    label: 'status',
    field: 'status',
    align: 'left',
    sortable: true,
  },
  {
    name: 'remote_hostname',
    label: 'remote_hostname',
    field: 'remote_hostname',
    align: 'left',
    sortable: true,
  },
  {
    name: 'username',
    label: 'username',
    field: 'username',
    align: 'left',
    sortable: true,
  },
  {
    name: 'password',
    label: 'password',
    field: 'password',
    align: 'left',
    sortable: true,
  },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];
</script>
