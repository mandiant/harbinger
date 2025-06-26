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
      <q-btn color="secondary" icon="refresh" @click="loadData">Refresh</q-btn>
      <q-btn color="secondary" icon="add_circle" to="issues/add">Add issue</q-btn>
    </div>
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Issues" :rows="data" row-key="id"
      :columns="columns" :loading="loading" v-model:pagination="pagination" @request="onRequest"
      :visible-columns="visible">
      <template v-slot:top>
        <div class="col-2 q-table__title">Issues</div>
        <q-space />
        <filter-view object-type="issues" v-model="filters" v-on:updateFilters="updateFilters" />
        <q-select v-model="visible" multiple borderless dense options-dense :display-value="$q.lang.table.columns"
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
      <template v-slot:body="props">
        <q-tr :props="props" class="cursor-pointer">
          <q-td key="id" :props="props">
            {{ props.row.id }}
          </q-td>
          <q-td key="name" :props="props">
            {{ props.row.name }}
          </q-td>
          <q-td key="description" :props="props">
            {{ props.row.description }}
          </q-td>
          <q-td key="impact" :props="props">
            {{ props.row.impact }}
          </q-td>
          <q-td key="exploitability" :props="props">
            {{ props.row.exploitability }}
          </q-td>
          <q-td key="time_created" :props="props">
            {{ props.row.time_created }}
          </q-td>
          <q-td key="time_updated" :props="props">
            {{ props.row.time_updated }}
          </q-td>
          <q-td key="label_id" :props="props">
            <label-button v-model="props.row.label_id"/>
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="issues" :object-id="String(props.row.id)" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { ref, toRaw } from 'vue';
import useloadData from 'src/load-data';
import { Issue } from 'src/models'
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import LabelButton from '../components/LabelButton.vue';
import { useCounterStore } from 'src/stores/object-counters';

const store = useCounterStore();

store.clear('issus');
const visible = ref(['id', 'name', 'description', 'impact', 'exploitability', 'time_created', 'time_updated', 'label_id'])

const { loading, data, pagination, loadData, onRequest, AddFilter } =
  useloadData<Array<Issue>>('issues');

const filters = ref({});

function updateFilters() {
  AddFilter(toRaw(filters.value));
  loadData();
}

loadData()

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: false },
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: false },
  { name: 'description', label: 'description', field: 'description', align: 'left', sortable: false },
  { name: 'impact', label: 'impact', field: 'impact', align: 'left', sortable: false },
  { name: 'exploitability', label: 'exploitability', field: 'exploitability', align: 'left', sortable: false },
  { name: 'time_created', label: 'time_created', field: 'time_created', align: 'left', sortable: false },
  { name: 'time_updated', label: 'time_updated', field: 'time_updated', align: 'left', sortable: false },
  { name: 'label_id', label: 'label', field: 'label_id', align: 'left', sortable: false },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

</script>