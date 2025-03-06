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
    <q-card-actions>
      <q-btn-dropdown
        class="q-ml-lg"
        color="secondary"
        label="Pre-defined queries"
        :loading="loading"
        icon="search"
      >
        <q-list>
          <q-item
            clickable
            v-close-popup
            v-for="item in data"
            v-bind:key="item.name"
            @click="performQuery(item.name)"
          >
            <q-item-section avatar>
              <q-avatar
                :icon="item.icon"
                color="secondary"
                text-color="white"
              />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ item.description }}</q-item-label>
            </q-item-section>
            <q-inner-loading :showing="loading">
              <q-spinner-gears size="50px" color="primary" />
            </q-inner-loading>
          </q-item>
        </q-list>
      </q-btn-dropdown>
      <q-btn @click="nodes = []" label="Clear" icon="clear" color="secondary" />
      <q-btn
        color="secondary"
        icon="archive"
        label="Export to json"
        v-if="nodes.length > 0"
        @click="exportTable"
      />
      <q-toggle
        v-model="owned_only"
        label="Display owned nodes only?"
        @update:model-value="performQuery(last)"
      />
    </q-card-actions>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]"
      title="Nodes"
      :rows="nodes"
      row-key="id"
      :loading="loading"
      :columns="columns"
      :filter="filter"
    >
      <template v-slot:top-right>
        <q-input
          borderless
          dense
          debounce="300"
          v-model="filter"
          placeholder="Search"
          autofocus
        >
          <template v-slot:append>
            <q-icon name="search" />
          </template>
        </q-input>
      </template>
      <template v-slot:header="props">
        <q-tr :props="props">
          <q-th auto-width />
          <q-th v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.label }}
          </q-th>
        </q-tr>
      </template>
      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td auto-width>
            <q-btn
              size="sm"
              color="accent"
              round
              dense
              :icon="formatIcon(props.row)"
            />
          </q-td>
          <q-td v-for="col in props.cols" :key="col.name" :props="props">
            {{ col.value }}
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-card>
</template>

<script setup lang="ts">
import useloadData from 'src/load-data';
import { Node, Query } from '../models';
import { api } from 'boot/axios';
import { ref } from 'vue';
import { exportFile, useQuasar } from 'quasar';
import { QTableProps } from 'quasar';

const $q = useQuasar();
const { loading, data, loadData } =
  useloadData<Array<Query>>('graph/pre-defined-queries');
const nodes = ref<Array<Node>>([]);
const owned_only = ref(false);
const filter = ref('');

const columns: QTableProps['columns'] = [
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true },
  {
    name: 'highvalue',
    label: 'highvalue',
    field: 'highvalue',
    align: 'left',
    sortable: true,
  },
  {
    name: 'extra',
    label: 'extra',
    field: 'extra',
    align: 'left',
    sortable: true,
  },
  {
    name: 'owned',
    label: 'owned',
    field: 'owned',
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
  {
    name: 'distinguishedname',
    label: 'distinguishedname',
    field: 'distinguishedname',
    align: 'left',
    sortable: true,
  },
];

loadData();

function formatIcon(row: Node) {
  if (!row.labels) {
    return '';
  }
  if (row.owned) {
    return 'fas fa-skull';
  }
  if (row.labels.includes('Group')) {
    return 'group';
  }
  if (row.labels.includes('Computer')) {
    return 'computer';
  }
  return 'person';
}

const last = ref('');

function performQuery(query: string) {
  if (query !== '') {
    last.value = query;
    loading.value = true;
    api
      .get(`/graph/pre-defined-queries/${query}`, {
        params: {
          owned_only: owned_only.value,
        },
      })
      .then((response) => {
        loading.value = false;
        nodes.value = response.data;
      })
      .catch(() => {
        loading.value = false;
        $q.notify({
          color: 'negative',
          position: 'top',
          message: 'Loading failed',
          icon: 'report_problem',
        });
      });
  }
}

function exportTable() {
  const status = exportFile(
    'table-export.json',
    JSON.stringify(nodes.value),
    'application/json'
  );

  if (status !== true) {
    $q.notify({
      message: 'Browser denied file download...',
      color: 'negative',
      icon: 'warning',
      position: 'top',
    });
  }
}
</script>
