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
    
    <q-btn color="secondary" icon="refresh" @click="loadData()">Refresh</q-btn>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]"
      title="Groups"
      :rows="data"
      row-key="id"
      :columns="columns"
      :loading="loading"
      v-model:pagination="pagination"
      @request="onRequest"
    >
      <template v-slot:top-right>
        <q-input
          borderless
          dense
          v-model="search"
          debounce="300"
          placeholder="Search"
          autofocus
        >
          <template v-slot:append>
            <q-icon name="search" />
          </template>
        </q-input>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

import useloadData from 'src/load-data';
import { GraphGroup } from '../models';
import { QTableProps } from 'quasar';

const { loading, data, pagination, loadData, onRequest, AddFilter } =
  useloadData<Array<GraphGroup>>('graph/groups');
const search = ref('');

AddFilter({ search: search.value });
loadData();

const columns: QTableProps['columns'] = [
  {
    name: 'name',
    label: 'name',
    field: 'name',
    align: 'left',
    sortable: true,
  },
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
];

// eslint-disable-next-line @typescript-eslint/no-unused-vars
watch(search, async (oldSearch, newSearch) => {
  AddFilter({ search: search.value });
  loadData();
});
</script>
