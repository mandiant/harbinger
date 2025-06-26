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
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Highlight" :rows="data" row-key="id"
      :columns="columns" :loading="loading" v-model:pagination="pagination" @request="store.onRequest"
      :visible-columns="visible">
      <template v-slot:top> 
        <div class="row items-center" style="width: 100%;">
          <div class="col-auto q-table__title">Highlights</div>
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
          <filter-view object-type="highlights" v-model="filters" @updateFilters="store.updateFilters"
            class="full-width" />
        </div>
      </template>
      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td key="id" :props="props">
            {{ props.row.id }}
          </q-td>
          <q-td key="hit" :props="props">
            {{ Truncate(props.row.hit) }}
          </q-td>
          <q-td key="time_created" :props="props">
            {{ props.row.time_created }}
          </q-td>
          <q-td key="rule_id" :props="props">
            {{ props.row.rule_id }}
          </q-td>
          <q-td key="rule_type" :props="props">
            {{ props.row.rule_type }}
          </q-td>
          <q-td key="link" :props="props">
            <q-btn color="secondary" icon="open_in_new" flat
              v-if="props.row.file_id || props.row.c2_task_id || props.row.proxy_job_id || props.row.c2_task_output_id" label="Open"
              @click="Goto(props.row)" />
          </q-td>
          <q-td key="start" :props="props">
            {{ props.row.start }}
          </q-td>
          <q-td key="end" :props="props">
            {{ props.row.end }}
          </q-td>
          <q-td key="line" :props="props">
            {{ props.row.line }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="highlights" :object-id="String(props.row.id)" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Highlight } from 'src/models'
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { useCounterStore } from 'src/stores/object-counters';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { Truncate } from 'src/truncate';

const counter_store = useCounterStore();
const $router = useRouter();

counter_store.clear('highlights');
const visible = ref(['hit', 'link', 'rule_type', 'labels'])

const useStore = defineTypedStore<Highlight>('highlights');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: false },
  { name: 'hit', label: 'hit', field: 'hit', align: 'left', sortable: false },
  { name: 'time_created', label: 'time_created', field: 'time_created', align: 'left', sortable: false },
  { name: 'rule_id', label: 'rule_id', field: 'rule_id', align: 'left', sortable: false },
  { name: 'rule_type', label: 'rule_type', field: 'rule_type', align: 'left', sortable: false },
  { name: 'link', label: 'link', field: 'link', align: 'left', sortable: false },
  { name: 'start', label: 'start', field: 'start', align: 'left', sortable: false },
  { name: 'end', label: 'end', field: 'end', align: 'left', sortable: false },
  { name: 'line', label: 'line', field: 'line', align: 'left', sortable: false },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

function Goto(row: Highlight) {
  if (row.file_id) {
    $router.push({ name: 'file', params: { id: row.file_id } });
  } else if (row.c2_task_id) {
    $router.push({ name: 'c2_task', params: { id: row.c2_task_id } });
  } else if (row.proxy_job_id) {
    $router.push({ name: 'proxy_job', params: { id: row.proxy_job_id } });
  } else if (row.c2_task_output_id) {
    $router.push({ name: 'c2_task_output', params: { id: row.c2_task_output_id } });
  }
}
</script>