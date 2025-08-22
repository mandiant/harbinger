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
    <q-btn color="secondary" icon="refresh" @click="store.LoadData">Refresh</q-btn>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Shares" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="store.onRequest" selection="multiple" v-model:selected="selected">
      <template v-slot:top>
        <div class="col-2 q-table__title" v-if="selected.length === 0">Shares</div>
        <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
            <bulk-label-actions :selected="selected" object-type="share" @update="selected = []; store.LoadData()" />
            <q-btn dense icon="clear" @click="selected = []" flat>
              <q-tooltip>Clear Selection</q-tooltip>
            </q-btn>
            <div>{{ selected.length }} item(s) selected</div>
          </div>
        <q-space />
        <filter-view v-if="selected.length === 0" object-type="shares" v-model="filters" v-on:updateFilters="store.updateFilters" />
      </template>
      <template v-slot:header-selection="scope">
        <q-checkbox v-model="scope.selected" />
      </template>
      <template v-slot:body="props">
        <q-tr :props="props" class="cursor-pointer">
            <q-td>
            <q-checkbox v-model="props.selected" />
          </q-td>
          <q-td key="unc_path" :props="props" @click="Goto(props.row)">
            {{ props.row.unc_path }}
          </q-td>
          <q-td key="name" :props="props" @click="Goto(props.row)">
            {{ props.row.name }}
          </q-td>
          <q-td key="type" :props="props" @click="Goto(props.row)">
            {{ props.row.type }}
          </q-td>
          <q-td key="remark" :props="props" @click="Goto(props.row)">
            {{ props.row.remark }}
          </q-td>
          <q-td key="time_created" :props="props" @click="Goto(props.row)">
            {{ props.row.time_created }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="share" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs } from 'vue';
import { Share } from 'src/models';
import { useRouter } from 'vue-router';
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import { useCounterStore } from 'src/stores/object-counters';
import FilterView from '../components/FilterView.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia';
import BulkLabelActions from './BulkLabelActions.vue';

const counter_store = useCounterStore();
const selected = ref([]);

counter_store.clear('shares');

const props = defineProps({
  host_id: {
    type: String,
    default: '',
  }
});

const $router = useRouter();
const { host_id } = toRefs(props);
const useStore = defineTypedStore<Share>('shares');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

if (host_id.value) {
  store.AddFilter({ host_id: host_id.value });
} else {
  store.RemoveFilter('host_id')
}

const columns: QTableProps['columns'] = [
{ name: 'unc_path', label: 'unc_path', field: 'unc_path', align: 'left', sortable: true },
{ name: 'name', label: 'name', field: 'name', align: 'left', sortable: true },
{ name: 'type', label: 'type', field: 'type', align: 'left', sortable: true },
{ name: 'remark', label: 'remark', field: 'remark', align: 'left', sortable: true },
{ name: 'time_created', label: 'time_created', field: 'time_created', align: 'left', sortable: true },
{
    name: 'labels',
    label: 'labels',
    field: 'labels',
    align: 'left',
    sortable: true,
  },
];

function Goto(row: Share) {
  $router.push({ name: 'share', params: { id: row.id } });
}

</script>
