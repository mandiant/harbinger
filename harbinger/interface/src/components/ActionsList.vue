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
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Actions" :rows="data" row-key="id"
      :columns="columns" :loading="loading" v-model:pagination="pagination" @request="store.onRequest"
      :visible-columns="visible">
      <template v-slot:top>
        <div class="col-2 q-table__title">Actions</div>
        <q-space />
        <filter-view object-type="actions" v-model="filters" v-on:updateFilters="store.updateFilters" />
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
          <q-td key="id" :props="props">
            {{ props.row.id }}
          </q-td>
          <q-td key="name" :props="props">
            {{ props.row.name }}
          </q-td>
          <q-td key="description" :props="props">
            {{ props.row.description }}
          </q-td>
          <q-td key="status" :props="props">
            <q-spinner-hourglass color="primary" v-if="props.row.status === 'queued'" />
            <q-spinner-hourglass color="primary" v-else-if="props.row.status === 'scheduled'" />
            <q-spinner-gears color="primary" v-else-if="props.row.status === 'running'" />
            <q-spinner-gears color="primary"
              v-else-if="props.row.status === 'processed, waiting for more messages...'" />
            <q-spinner-gears color="primary" v-else-if="props.row.status === 'processed'" />
            <q-spinner-gears color="primary" v-else-if="props.row.status === 'processing'" />
            <q-spinner-gears color="primary" v-else-if="props.row.status === 'submitted'" />
            <q-icon name="check" color="green" v-else-if="props.row.status === 'completed'" />
            <q-icon name="close" color="red" v-else-if="props.row.status === 'error'" />
          </q-td>
          <q-td key="time_created" :props="props">
            {{ props.row.time_created }}
          </q-td>
          <q-td key="time_updated" :props="props">
            {{ props.row.time_updated }}
          </q-td>
          <q-td key="time_started" :props="props">
            {{ props.row.time_started }}
          </q-td>
          <q-td key="time_completed" :props="props">
            {{ props.row.time_completed }}
          </q-td>
          <q-td key="actions" :props="props">
            <q-btn-dropdown flat color="secondary" icon="add" label="Create playbook">
              <q-list v-for="(value, index) in props.row.playbook_templates" v-bind:key="index">
                <q-item clickable v-close-popup @click="CreatePlaybook(value)">
                  <q-item-section avatar>
                    <q-icon color="secondary" :name="value.icon" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>{{ value.name }}</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-btn-dropdown>
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="action" :object-id="String(props.row.id)" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Action, Template } from 'src/models'
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { useParamStore } from 'src/stores/ParamStore';
import { useRouter } from 'vue-router';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const p_store = useParamStore();
const $router = useRouter();

const visible = ref(['name', 'description', 'status', 'time_started', 'time_completed', 'actions', 'labels'])

const useStore = defineTypedStore<Action>('actions');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true },
  { name: 'description', label: 'description', field: 'description', align: 'left', sortable: true },
  { name: 'status', label: 'status', field: 'status', align: 'left', sortable: true },
  { name: 'time_created', label: 'time_created', field: 'time_created', align: 'left', sortable: true },
  { name: 'time_updated', label: 'time_updated', field: 'time_updated', align: 'left', sortable: true },
  { name: 'time_started', label: 'time_started', field: 'time_started', align: 'left', sortable: true },
  { name: 'time_completed', label: 'time_completed', field: 'time_completed', align: 'left', sortable: true },
  { name: 'actions', label: 'actions', field: 'actions', align: 'left', sortable: false },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

function CreatePlaybook(row: Template) {
  p_store.setPlaybookTemplate(row.id)
  $router.push({ name: 'add_playbook_from_template' });
}

</script>
