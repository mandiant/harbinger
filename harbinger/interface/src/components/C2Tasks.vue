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
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Tasks" :rows="data" row-key="id" :columns="columns" :loading="loading" v-model:pagination="pagination"
      @request="store.onRequest" :visible-columns="visible">
      <template v-slot:top>
        <div class="col-2 q-table__title">Tasks</div>
        <q-space />
        <filter-view object-type="c2/tasks" v-model="filters" v-on:updateFilters="store.updateFilters" />
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
        <q-tr :props="props" class="cursor-pointer">
          <q-td key="id" :props="props" @click="Goto(props.row)">
            {{ props.row.id }}
          </q-td>
          <q-td key="command_name" :props="props" @click="Goto(props.row)">
            {{ props.row.command_name }}
          </q-td>
          <q-td key="operator" :props="props" @click="Goto(props.row)">
            {{ props.row.operator }}
          </q-td>
          <q-td key="status" :props="props" @click="Goto(props.row)">
            {{ props.row.status }}
          </q-td>
          <q-td key="processing_status" :props="props" @click="Goto(props.row)">
            {{ props.row.processing_status }}
          </q-td>
          <q-td key="ai_summary" :props="props" @click="Goto(props.row)">
            {{ props.row.ai_summary }}
          </q-td>
          <q-td key="original_params" :props="props" @click="Goto(props.row)">
            {{ Truncate(props.row.original_params) }}
          </q-td>
          <q-td key="display_params" :props="props" @click="Goto(props.row)">
            {{ Truncate(props.row.display_params) }}
          </q-td>
          <q-td key="time_started" :props="props" @click="Goto(props.row)">
            {{ props.row.time_started }}
          </q-td>
          <q-td key="time_started" :props="props" @click="Goto(props.row)">
            {{ props.row.time_started }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="c2_task" :object-id="String(props.row.id)" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { toRefs, ref } from 'vue';
import { C2Task } from 'src/models'
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import { useRouter } from 'vue-router';
import FilterView from '../components/FilterView.vue';
import { Truncate } from 'src/truncate';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const props = defineProps({
  implant_id: {
    type: String,
    default: '',
  },
});

const { implant_id } = toRefs(props);

const visible = ref(['command_name', 'operator', 'status', 'display_params', 'time_started', 'time_completed', 'labels'])

const useStore = defineTypedStore<C2Task>('c2/tasks');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const $router = useRouter();

if (implant_id.value) {
  store.AddFilter({ c2_implant_id: implant_id.value })
} else {
  store.RemoveFilter('c2_implant_id')
}

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  { name: 'command_name', label: 'command_name', field: 'command_name', align: 'left', sortable: true },
  { name: 'operator', label: 'operator', field: 'operator', align: 'left', sortable: true },
  { name: 'status', label: 'status', field: 'status', align: 'left', sortable: true },
  { name: 'processing_status', label: 'processing_status', field: 'processing_status', align: 'left', sortable: false },
  { name: 'ai_summary', label: 'ai_summary', field: 'ai_summary', align: 'left', sortable: false },
  { name: 'original_params', label: 'original_params', field: 'original_params', align: 'left', sortable: true },
  { name: 'display_params', label: 'display_params', field: 'display_params', align: 'left', sortable: true },
  { name: 'time_started', label: 'time_started', field: 'time_started', align: 'left', sortable: true },
  { name: 'time_completed', label: 'time_completed', field: 'time_completed', align: 'left', sortable: true },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

function Goto(row: C2Task) {
  if (implant_id.value) {
    $router.push({ name: 'implant_task', params: { id: implant_id.value, task_id: row.id } });
  } else {
    $router.push({ name: 'c2_task', params: { task_id: row.id } });
  }
}

</script>
