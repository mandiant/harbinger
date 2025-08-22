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
    <div class="row q-gutter-sm">
      <q-btn color="secondary" icon="refresh" @click="store.LoadData">Refresh</q-btn>
      <q-btn color="secondary" icon="add_circle" to="suggestions/add">Create suggestions</q-btn>
    </div>
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Suggestions" :rows="data" row-key="id"
      :columns="columns" :loading="loading" v-model:pagination="pagination" @request="store.onRequest"
      :visible-columns="visible" selection="multiple" v-model:selected="selected">
      <template v-slot:top>
        <div class="col-2 q-table__title" v-if="selected.length === 0">Suggestions</div>
        <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
            <bulk-label-actions :selected="selected" object-type="suggestion" @update="selected = []; store.LoadData()" />
            <q-btn dense icon="clear" @click="selected = []" flat>
              <q-tooltip>Clear Selection</q-tooltip>
            </q-btn>
            <div>{{ selected.length }} item(s) selected</div>
          </div>
        <q-space />
        <filter-view v-if="selected.length === 0" object-type="suggestions" v-model="filters" v-on:updateFilters="store.updateFilters" />
        <q-select v-if="selected.length === 0" v-model="visible" multiple borderless dense options-dense :display-value="$q.lang.table.columns"
          emit-value map-options :options="columns" option-value="name" style="min-width: 150px">
          <template v-slot:option="{ itemProps, opt, selected, toggleOption }">
            <q-item v-bind="itemProps">
              <q-item-section>
                <q-item-label :class="$q.dark.isActive ? 'text-white' : 'text-black'">
                  {{ opt.label }}
                </q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-toggle :model-value="selected" @update:model-value="toggleOption(opt)" />
              </q-item-section>
            </q-item>
          </template>
        </q-select>
      </template>
      <template v-slot:header-selection="scope">
        <q-checkbox v-model="scope.selected" />
      </template>
      <template v-slot:body="props">
        <q-tr :props="props" class="cursor-pointer">
            <q-td>
            <q-checkbox v-model="props.selected" />
          </q-td>
          <q-td key="id" :props="props">
            {{ props.row.id }}
          </q-td>
          <q-td key="name" :props="props" @click="Goto(props.row)">
            {{ props.row.name }}
          </q-td>
          <q-td key="reason" :props="props" @click="Goto(props.row)">
            {{ Truncate(props.row.reason) }}
          </q-td>
          <q-td key="playbook_template_id" :props="props" @click="Goto(props.row)">
            {{ props.row.playbook_template_id }}
          </q-td>
          <q-td key="arguments" :props="props" @click="Goto(props.row)">
            {{ props.row.arguments }}
          </q-td>
          <q-td key="time_created" :props="props" @click="Goto(props.row)">
            {{ props.row.time_created }}
          </q-td>
          <q-td key="time_updated" :props="props" @click="Goto(props.row)">
            {{ props.row.time_updated }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="suggestion" :object-id="String(props.row.id)" v-model="props.row.labels" />
          </q-td>
          <q-td key="actions" :props="props">
            <q-btn flat color="secondary" icon="add_circle" label="Create playbook"
              :to="{ name: 'suggestion_create', params: { id: props.row.id } }" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Suggestion } from 'src/models'
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { useCounterStore } from 'src/stores/object-counters';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'
import { Truncate } from 'src/truncate';
import { useRouter } from 'vue-router';
import BulkLabelActions from './BulkLabelActions.vue';

const counter_store = useCounterStore();
const selected = ref([]);

counter_store.clear('suggestions');
const visible = ref(['name', 'reason', 'labels', 'actions', 'time_created'])
const $router = useRouter();

const useStore = defineTypedStore<Suggestion>('suggestions');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: false },
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: false },
  { name: 'reason', label: 'reason', field: 'reason', align: 'left', sortable: false },
  { name: 'playbook_template_id', label: 'playbook_template_id', field: 'playbook_template_id', align: 'left', sortable: false },
  { name: 'arguments', label: 'arguments', field: 'arguments', align: 'left', sortable: false },
  { name: 'time_created', label: 'time_created', field: 'time_created', align: 'left', sortable: false },
  { name: 'time_updated', label: 'time_updated', field: 'time_updated', align: 'left', sortable: false },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
  { name: 'actions', label: 'actions', field: 'actions', align: 'left', sortable: false },
];

function Goto(row: Suggestion) {
  $router.push({ name: 'suggestion', params: { id: row.id } });
}

</script>