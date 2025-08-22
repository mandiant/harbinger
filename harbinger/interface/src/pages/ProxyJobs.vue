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
      <q-btn color="secondary" icon="add_circle" to="proxy_jobs/add">Create new job</q-btn>
      <q-btn color="secondary" icon="add_circle" to="proxy_jobs/add_from_template">Create from template</q-btn>
      <q-btn color="secondary" icon="refresh" @click="store.LoadData()">Refresh</q-btn>
    </div>
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Socks Jobs" :rows="data" row-key="id"
      :columns="columns" :loading="loading" v-model:pagination="pagination" @request="store.onRequest"
      :visible-columns="visible">
      <template v-slot:top> 
        <div class="row items-center" style="width: 100%;">
          <div class="col-auto q-table__title">Socks Jobs</div>
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
          <filter-view object-type="proxy_jobs" v-model="filters" @updateFilters="store.updateFilters"
            class="full-width" />
        </div>
      </template>
      <template v-slot:body="props">
        <q-tr :props="props" class="cursor-pointer">
          <q-td key="id" :props="props" @click="Goto(props.row)">
            {{ props.row.id }}
          </q-td>
          <q-td key="command" :props="props" @click="Goto(props.row)">
            {{ props.row.command }}
          </q-td>
          <q-td key="arguments" :props="props" @click="Goto(props.row)">
            {{ Truncate(props.row.arguments) }}
          </q-td>
          <q-td key="status" :props="props" @click="Goto(props.row)">
            {{ props.row.status }}
          </q-td>
          <q-td key="processing_status" :props="props">
            {{ props.row.processing_status }}
          </q-td>
          <q-td key="ai_summary" :props="props">
            {{ props.row.ai_summary }}
          </q-td>
          <q-td key="credential_id" :props="props" @click="Goto(props.row)">
            {{ props.row.credential_id }}
          </q-td>
          <q-td key="proxy_id" :props="props" @click="Goto(props.row)">
            {{ props.row.proxy_id }}
          </q-td>
          <q-td key="files" :props="props" @click="Goto(props.row)">
            <q-chip icon="description" color="tertiary" v-for="file in props.row.files" v-bind:key="file.id">{{
              file.filename }}</q-chip>
          </q-td>
          <q-td key="input_files" :props="props" @click="Goto(props.row)">
            <q-chip icon="description" color="tertiary" v-for="file in props.row.input_files" v-bind:key="file.id">{{
              file.filename }}</q-chip>
          </q-td>
          <q-td key="playbook_id" :props="props" @click="Goto(props.row)">
            {{ props.row.playbook_id }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="proxy_job" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
          <q-menu context-menu touch-position>
            <q-list style="min-width: 100px">
              <q-item clickable v-close-popup @click="Goto(props.row)">
                <q-item-section avatar>
                  <q-icon color="secondary" name="open_in_new" />
                </q-item-section>
                <q-item-section>Go to socks job</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="Clone(props.row)">
                <q-item-section avatar>
                  <q-icon color="secondary" name="content_copy" />
                </q-item-section>
                <q-item-section>Clone</q-item-section>
              </q-item>
              <q-item clickable v-close-popup v-if="props.row.playbook_id > 0" @click="GotoChain(props.row)">
                <q-item-section avatar>
                  <q-icon color="secondary" name="open_in_new" />
                </q-item-section>
                <q-item-section>Go to playbook</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="start(props.row)" v-if="props.row.status === 'created'">
                <q-item-section avatar>
                  <q-icon color="secondary" name="play_arrow" />
                </q-item-section>
                <q-item-section>Start</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

import { ProxyJob } from '../models';
import { useQuasar } from 'quasar';
import { api } from 'boot/axios';
import { useCounterStore } from 'src/stores/object-counters';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { Truncate } from 'src/truncate';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const counter_store = useCounterStore();

counter_store.clear('proxy_jobs');

const $q = useQuasar();

const useStore = defineTypedStore<ProxyJob>('proxy_jobs');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const $router = useRouter();

const visible = ref(['id', 'command', 'arguments', 'status', 'labels', 'input_files']);

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  { name: 'command', label: 'command', field: 'command', align: 'left' },
  { name: 'arguments', label: 'arguments', field: 'arguments', align: 'left' },
  { name: 'status', label: 'status', field: 'status', align: 'left' },
  { name: 'processing_status', label: 'processing_status', field: 'processing_status', align: 'left', sortable: false },
  { name: 'ai_summary', label: 'ai_summary', field: 'ai_summary', align: 'left', sortable: false },
  {
    name: 'credential_id',
    label: 'credential_id',
    field: 'credential_id',
    align: 'left',
  },
  { name: 'proxy_id', label: 'proxy_id', field: 'proxy_id', align: 'left' },
  {
    name: 'files',
    label: 'files',
    field: (row: ProxyJob) => (row.files.length > 0 ? row.files.length : ''),
    align: 'left',
  },
  {
    name: 'input_files',
    label: 'input_files',
    field: (row: ProxyJob) =>
      row.input_files !== null ? row.input_files.length : '',
    align: 'left',
  },
  {
    name: 'playbook_id',
    label: 'playbook_id',
    field: 'playbook_id',
    align: 'left',
  },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

function Goto(row: ProxyJob) {
  $router.push({ name: 'proxy_job', params: { id: row.id } });
}
function GotoChain(row: ProxyJob) {
  $router.push({ name: 'playbook', params: { id: row.playbook_id } });
}

function Clone(row: ProxyJob) {
  loading.value = true;
  api
    .post(`/proxy_jobs/${row.id}/clone`)
    .then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: 'Cloned job',
        position: 'top',
      });
      loading.value = false;
    })
    .catch((error) => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: `Failed to start: ${error.response.data.error}`,
        icon: 'report_problem',
      });
    });
}

function start(row: ProxyJob) {
  loading.value = true;
  api
    .post(`/proxy_jobs/${row.id}/start`)
    .then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: 'Started job',
        position: 'top',
      });
      loading.value = false;
    })
    .catch((error) => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: `Failed to start: ${error.response.data.error}`,
        icon: 'report_problem',
      });
    });
}
</script>
