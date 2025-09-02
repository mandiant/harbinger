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
      <q-btn color="secondary" icon="refresh" @click="timelineStore.LoadData()">Refresh</q-btn>
      <q-btn color="secondary" icon="add_circle" to="timeline/add">Add entry</q-btn>
      <q-btn color="secondary" icon="add_circle" to="timeline/create">Create timeline document</q-btn>
      <q-btn color="secondary" icon="memory" @click="createSummaries()">Create summaries</q-btn>
    </div>
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="ManualTimelineTask" :rows="data" row-key="id"
    :columns="columns" :loading="loading" v-model:pagination="pagination" @request="timelineStore.onRequest"
    :visible-columns="visible">
      <template v-slot:top>
        <div class="col-2 q-table__title">Timeline</div>
        <q-space />
        <filter-view object-type="timeline" v-model="filters" v-on:updateFilters="timelineStore.updateFilters" />
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
          <q-td key="object_type" :props="props">
            {{ props.row.object_type }}
          </q-td>
          <q-td key="hostname" :props="props">
            {{ props.row.hostname }}
          </q-td>
          <q-td key="command_name" :props="props">
            {{ props.row.command_name }}
          </q-td>
          <q-td key="arguments" :props="props">
            {{ Truncate(props.row.arguments) }}
          </q-td>
          <q-td key="argument_params" :props="props">
            {{ props.row.argument_params }}
          </q-td>
          <q-td key="status" :props="props">
            {{ props.row.status }}
          </q-td>
          <q-td key="processing_status" :props="props">
            {{ props.row.processing_status }}
          </q-td>
          <q-td key="ai_summary" :props="props">
            {{ props.row.ai_summary }}
          </q-td>
          <q-td key="operator" :props="props">
            {{ props.row.operator }}
          </q-td>
          <q-td key="time_started" :props="props">
            {{ props.row.time_started }}
          </q-td>
          <q-td key="time_completed" :props="props">
            {{ props.row.time_completed }}
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';

import { Timeline } from '../models';
import { QTableProps } from 'quasar';
import { Truncate } from 'src/truncate';
import FilterView from '../components/FilterView.vue';
import { ref } from 'vue';
import { api } from 'boot/axios';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const $q = useQuasar();

const useTimeline = defineTypedStore<Timeline>('timeline');
const timelineStore = useTimeline();

const { loading, data, pagination, filters } = storeToRefs(timelineStore);

const visible = ref(['object_type', 'hostname', 'command_name', 'arguments', 'status', 'operator', 'time_completed'])

timelineStore.Load();
const columns: QTableProps['columns'] = [
  { name: 'object_type', label: 'Type', field: 'object_type', align: 'left', sortable: false },
  { name: 'hostname', label: 'Hostname', field: 'hostname', align: 'left', sortable: false },
  { name: 'command_name', label: 'Command', field: 'command_name', align: 'left', sortable: false },
  { name: 'arguments', label: 'arguments', field: 'arguments', align: 'left', sortable: false },
  { name: 'argument_params', label: 'argument_params', field: 'argument_params', align: 'left', sortable: false },
  { name: 'status', label: 'status', field: 'status', align: 'left', sortable: false },
  { name: 'processing_status', label: 'processing_status', field: 'processing_status', align: 'left', sortable: false },
  { name: 'ai_summary', label: 'ai_summary', field: 'ai_summary', align: 'left', sortable: false },
  { name: 'operator', label: 'operator', field: 'operator', align: 'left', sortable: false },
  { name: 'time_started', label: 'time_started', field: 'time_started', align: 'left', sortable: false },
  { name: 'time_completed', label: 'time_completed', field: 'time_completed', align: 'left', sortable: true },
];

function createSummaries() {
  api
    .post('/create_summaries/', data)
    .then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        message: 'Summarizing scheduled',
        position: 'top',
      });
      loading.value = false;
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Starting failed',
        icon: 'report_problem',
      });
    });
}

</script>
