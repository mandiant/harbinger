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
      <q-btn color="secondary" icon="add_circle" to="c2_jobs/add_from_template">Create new C2 job</q-btn>
      <q-btn color="secondary" icon="refresh" @click="store.LoadData()">Refresh</q-btn>
    </div>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="C2 Jobs" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="store.onRequest" :visible-columns="visible" selection="multiple" v-model:selected="selected">
      <template v-slot:top>
        <div class="row items-center" style="width: 100%;">
          <div class="col-auto q-table__title" v-if="selected.length === 0">C2 Jobs</div>
          <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
            <bulk-label-actions :selected="selected" object-type="c2_job" @update="selected = []; store.LoadData()" />
            <q-btn dense icon="clear" @click="selected = []" flat>
              <q-tooltip>Clear Selection</q-tooltip>
            </q-btn>
            <div>{{ selected.length }} item(s) selected</div>
          </div>
          <q-space />
          <q-select v-if="selected.length === 0" v-model="visible" multiple borderless dense options-dense
            :display-value="$q.lang.table.columns" emit-value map-options :options="columns" option-value="name"
            style="min-width: 150px">
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
          <filter-view v-if="selected.length === 0" object-type="c2_jobs" v-model="filters"
            @updateFilters="store.updateFilters" class="full-width" />
        </div>
      </template>
      <template v-slot:header-selection="scope">
        <q-checkbox v-model="scope.selected" />
      </template>
      <template v-slot:body="props">
        <q-tr :props="props" class="cursor-pointer">
          <q-td>
            <q-checkbox v-model="props.selected" />
          </q-td>
          <q-td key="id" :props="props" @click="Goto(props.row)">
            {{ props.row.id }}
          </q-td>
          <q-td key="command" :props="props" @click="Goto(props.row)">
            {{ props.row.command }}
          </q-td>
          <q-td key="arguments" :props="props" @click="Goto(props.row)">
            {{ Truncate(props.row.arguments) }}
          </q-td>
          <q-td key="implant" :props="props" @click="Goto(props.row)">
            {{props.row.c2_implant_id }}
          </q-td>
          <q-td key="status" :props="props" @click="Goto(props.row)">
            {{ props.row.status }}
          </q-td>
          <q-td key="message" :props="props" @click="Goto(props.row)">
            {{ props.row.message }}
          </q-td>
          <q-td key="playbook_id" :props="props" @click="Goto(props.row)">
            {{ props.row.playbook_id }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="c2_job" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
          <q-menu context-menu touch-position>
            <q-list style="min-width: 100px">
              <q-item clickable v-close-popup @click="Goto(props.row)">
                <q-item-section avatar>
                  <q-icon color="secondary" name="open_in_new" />
                </q-item-section>
                <q-item-section>Go to job</q-item-section>
              </q-item>

              <q-item clickable v-close-popup @click="start(props.row)" v-if="props.row.status === 'created'">
                <q-item-section avatar>
                  <q-icon color="secondary" name="play_arrow" />
                </q-item-section>
                <q-item-section>Start</q-item-section>
              </q-item>

              <q-item clickable v-close-popup @click="clone(props.row)">
                <q-item-section avatar>
                  <q-icon color="secondary" name="content_copy" />
                </q-item-section>
                <q-item-section>Clone</q-item-section>
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
import { C2Job } from '../models';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { useCounterStore } from 'src/stores/object-counters';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import { Truncate } from 'src/truncate';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia';
import FilterView from '../components/FilterView.vue';
import BulkLabelActions from 'src/components/BulkLabelActions.vue';


const counter_store = useCounterStore();
const selected = ref([]);

counter_store.clear('c2_jobs');

const $q = useQuasar();

const useStore = defineTypedStore<C2Job>('c2_jobs');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();


const $router = useRouter();

const visible = ref(['command', 'arguments', 'implant', 'status', 'labels']);

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  {
    name: 'command',
    label: 'command',
    field: 'command',
    align: 'left',
    sortable: true,
  },
  {
    name: 'arguments',
    label: 'arguments',
    field: 'arguments',
    align: 'left',
    sortable: true,
  },
  {
    name: 'implant',
    label: 'implant',
    field: 'implant',
    align: 'left',
    sortable: true,
  },
  {
    name: 'status',
    label: 'status',
    field: 'status',
    align: 'left',
    sortable: true,
  },
  {
    name: 'message',
    label: 'message',
    field: 'message',
    align: 'left',
    sortable: true,
  },
  {
    name: 'playbook_id',
    label: 'playbook_id',
    field: 'playbook_id',
    align: 'left',
    sortable: true,
  },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];


function Goto(row: C2Job) {
  $router.push({ name: 'c2_job', params: { id: row.id } });
}

function start(row: C2Job) {
  api
    .post(`/c2/jobs/${row.id}/start`)
    .then(() => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: 'Started',
        position: 'top',
      });
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

function clone(row: C2Job) {
  api
    .post(`/c2/jobs/${row.id}/clone`)
    .then(() => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: 'Cloned job',
        position: 'top',
      });
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
