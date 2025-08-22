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
      <q-btn color="secondary" icon="add_circle" to="domains/add">Add domain</q-btn>
      <q-btn color="secondary" icon="refresh" @click="domainStore.LoadData()">Refresh</q-btn>
    </div>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Domains" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="domainStore.onRequest">
      <template v-slot:top>
        <div class="col-2 q-table__title">Domains</div>
        <q-space />
        <filter-view object-type="domains" v-model="filters" v-on:updateFilters="domainStore.updateFilters" />
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
    </template>
      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td key="id" :props="props">
            {{ props.row.id }}
          </q-td>
          <q-td key="short_name" :props="props">
            {{ props.row.short_name }}
            <q-popup-edit v-model="props.row.short_name" title="Update short name" buttons v-slot="scope"
              @save="Save(props.row)">
              <q-input v-model="scope.value" dense autofocus />
            </q-popup-edit>
          </q-td>
          <q-td key="long_name" :props="props">
            {{ props.row.long_name }}
            <q-popup-edit v-model="props.row.long_name" title="Update long name" buttons v-slot="scope"
              @save="Save(props.row)">
              <q-input v-model="scope.value" dense autofocus />
            </q-popup-edit>
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="domain" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import { Domain } from '../models';
import { useCounterStore } from 'src/stores/object-counters';
import { QTableProps } from 'quasar';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const store = useCounterStore();

const useDomains = defineTypedStore<Domain>('domains');
const domainStore = useDomains();
const visible = ref(['short_name', 'long_name', 'time_created'])

domainStore.Load()

store.clear('domains');
const $q = useQuasar();

const { loading, data, pagination, filters } =
  storeToRefs(domainStore)

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  {
    name: 'short_name',
    label: 'short_name',
    field: 'short_name',
    align: 'left',
    sortable: true,
  },
  {
    name: 'long_name',
    label: 'long_name',
    field: 'long_name',
    align: 'left',
    sortable: true,
  },
  {
    name: 'labels',
    label: 'labels',
    field: '',
    align: 'left',
  },
];

function Save(row: Domain) {
  setTimeout(function () {
    api.put(`/domains/${row.id}`, { long_name: row.long_name, short_name: row.short_name }).then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        position: 'top',
        message: 'Updated domain',
      });
    }).catch(() => {
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Error updating domain',
        icon: 'report_problem',
      });
    });
  }, 100);
}
</script>
