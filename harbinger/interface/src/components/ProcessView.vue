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
  <div>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Processes" :rows="data" row-key="id" :loading="loading" :columns="columns"
      v-model:pagination="pagination" @request="onRequest" selection="multiple" v-model:selected="selected">
      <template v-slot:top>
        <div class="col-2 q-table__title" v-if="selected.length === 0">Processes</div>
        <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
            <bulk-label-actions :selected="selected" object-type="process" @update="selected = []; loadData()" />
            <q-btn dense icon="clear" @click="selected = []" flat>
              <q-tooltip>Clear Selection</q-tooltip>
            </q-btn>
            <div>{{ selected.length }} item(s) selected</div>
          </div>
        <q-space />
        <q-input v-if="selected.length === 0" borderless dense debounce="500" v-model="search" placeholder="Search" autofocus>
          <template v-slot:append>
            <q-icon name="search" />
          </template>
        </q-input>
        <q-toggle v-if="selected.length === 0" dense label="Labels" v-model="labels_only"/>
      </template>
      <template v-slot:header-selection="scope">
        <q-checkbox v-model="scope.selected" />
      </template>
      <template v-slot:body="props">
        <q-tr :props="props">
            <q-td>
            <q-checkbox v-model="props.selected" />
          </q-td>
          <q-td key="parent_process_id" :props="props">
            {{ props.row.parent_process_id }}
          </q-td>
          <q-td key="process_id" :props="props">
            {{ props.row.process_id }}
          </q-td>
          <q-td key="architecture" :props="props">
            {{ props.row.architecture }}
          </q-td>
          <q-td key="name" :props="props">
            {{ props.row.name }}
          </q-td>
          <q-td key="user" :props="props">
            {{ props.row.user }}
          </q-td>
          <q-td key="description" :props="props">
            {{ props.row.description }}
          </q-td>
          <q-td key="commandline" :props="props">
            {{ props.row.commandline }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="process" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { watch, toRefs, ref } from 'vue';
import useloadData from '../load-data';
import { Process } from '../models';
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import BulkLabelActions from './BulkLabelActions.vue';

const { loading, data, pagination, loadData, onRequest, AddFilter } =
  useloadData<Array<Process>>('processes');

const selected = ref([]);
const search = ref('')
const labels_only = ref(false)

const props = defineProps({
  host_id: {
    type: String,
    default: '',
  },
  implant_id: {
    type: String,
    default: '',
  },
  number: {
    type: Number,
    default: 0,
  },
});

const { host_id, implant_id, number } = toRefs(props);

const columns: QTableProps['columns'] = [
  {
    name: 'parent_process_id',
    label: 'parent_process_id',
    field: 'parent_process_id',
    align: 'left',
    sortable: true,
    style: 'width: 20px',
  },
  {
    name: 'process_id',
    label: 'process_id',
    field: 'process_id',
    align: 'left',
    sortable: true,
    style: 'width: 20px',
  },
  {
    name: 'architecture',
    label: 'architecture',
    field: 'architecture',
    align: 'left',
    sortable: true,
    style: 'width: 40px',
  },
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true },
  { name: 'user', label: 'user', field: 'user', align: 'left', sortable: true },
  {
    name: 'description',
    label: 'description',
    field: 'description',
    align: 'left',
    sortable: true,
  },
  {
    name: 'commandline',
    label: 'commandline',
    field: 'commandline',
    align: 'left',
    sortable: true,
  },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

watch(number, async () => {
  data.value = [];
  AddFilter({
    host_id: host_id.value,
    implant_id: implant_id.value,
    number: number.value,
  });
  loadData();
});

watch(labels_only, async () => {
  AddFilter({
    labels_only: labels_only.value
  });
  loadData();
});

watch(search, async () => {
  AddFilter({
    search: search.value
  });
  loadData();
});


AddFilter({
  host_id: host_id.value,
  implant_id: implant_id.value,
  number: number.value,
});
loadData();
</script>
