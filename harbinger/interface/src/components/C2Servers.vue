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
  <div class="row q-gutter-sm">
    <q-btn color="secondary" icon="add_circle" to="servers/add">Add C2 server</q-btn>
    <q-btn color="secondary" icon="refresh" @click="store.LoadData()">Refresh</q-btn>
  </div>
  <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="C2 Servers" :rows="data" row-key="id" :columns="columns" :loading="loading"
    v-model:pagination="pagination" @request="store.onRequest" selection="multiple" v-model:selected="selected">
    <template v-slot:top>
        <div class="col-2 q-table__title" v-if="selected.length === 0">C2 Servers</div>
        <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
            <bulk-label-actions :selected="selected" object-type="c2_server" @update="selected = []; store.LoadData()" />
            <q-btn dense icon="clear" @click="selected = []" flat>
              <q-tooltip>Clear Selection</q-tooltip>
            </q-btn>
            <div>{{ selected.length }} item(s) selected</div>
          </div>
        <q-space />
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
        <q-td key="type" :props="props" @click="Goto(props.row)">
          {{ props.row.type }}
        </q-td>
        <q-td key="name" :props="props" @click="Goto(props.row)">
          {{ props.row.name }}
        </q-td>
        <q-td key="hostname" :props="props" @click="Goto(props.row)">
          {{ props.row.hostname }}
        </q-td>
        <q-td key="username" :props="props" @click="Goto(props.row)">
          {{ props.row.username }}
        </q-td>
        <q-td key="port" :props="props" @click="Goto(props.row)">
          {{ props.row.port }}
        </q-td>
        <q-td key="status" :props="props">
          <q-btn-dropdown :loading="loading" flat color="secondary"
            :icon="status_to_icon(value.status)" :label="value.name"
            v-for="(value, index) in props.row.status" v-bind:key="index">
            <q-list>
              <q-item>
                <q-item-section avatar>
                  <q-icon color="secondary" name="monitor_heart" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>{{ value.status }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item v-if="value.status !== 'running'" clickable v-close-popup @click="run_command(props.row.id, value.name, 'start')">
                <q-item-section avatar>
                  <q-icon color="secondary" name="play_arrow" />
                </q-item-section>

                <q-item-section>
                  <q-item-label>Start</q-item-label>
                </q-item-section>
              </q-item>

              <q-item v-if="value.status !== 'exited'" clickable v-close-popup @click="run_command(props.row.id, value.name, 'stop')">
                <q-item-section avatar>
                  <q-icon color="secondary" name="stop" />
                </q-item-section>

                <q-item-section>
                  <q-item-label>Stop</q-item-label>
                </q-item-section>
              </q-item>

              <q-item v-if="value.status === 'running'" clickable v-close-popup @click="run_command(props.row.id, value.name, 'restart')">
                <q-item-section avatar>
                  <q-icon color="secondary" name="replay" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Restart</q-item-label>
                </q-item-section>
              </q-item>

              <q-item clickable v-close-popup @click="run_command(props.row.id, value.name, 'delete')">
                <q-item-section avatar>
                  <q-icon color="secondary" name="delete" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Delete</q-item-label>
                </q-item-section>
              </q-item>

              <q-item clickable v-close-popup @click="run_command(props.row.id, value.name, 'sync')">
                <q-item-section avatar>
                  <q-icon color="secondary" name="sync" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>Sync All</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
          <q-btn flat color="secondary" v-if="props.row.status.length === 0" icon="add_circle" label="Create container"
            @click="run_command(props.row.id, '', 'create')" :loading="loading" />
        </q-td>
        <q-td key="labels" :props="props">
          <labels-list object-type="c2_server" :object-id="String(props.row.id)" v-model="props.row.labels" />
        </q-td>
      </q-tr>
    </template>
  </q-table>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { C2Server } from '../models';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import { useRouter } from 'vue-router';
import { useCounterStore } from 'src/stores/object-counters';
import { api } from 'src/boot/axios';
import { useQuasar } from 'quasar';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia';
import BulkLabelActions from './BulkLabelActions.vue';

const $q = useQuasar();
const counter_store = useCounterStore();
const selected = ref([]);

counter_store.clear('c2_servers');

const useStore = defineTypedStore<C2Server>('c2_servers');
const store = useStore();
const { loading, data, pagination,  } = storeToRefs(store);
store.Load();

const $router = useRouter();

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  { name: 'type', label: 'type', field: 'type', align: 'left', sortable: true },
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true },
  {
    name: 'hostname',
    label: 'hostname',
    field: 'hostname',
    align: 'left',
    sortable: true,
  },
  {
    name: 'username',
    label: 'username / engagement id',
    field: 'username',
    align: 'left',
    sortable: true,
  },
  { name: 'port', label: 'port', field: 'port', align: 'left', sortable: true },
  {
    name: 'status',
    label: 'status',
    field: 'status',
    align: 'left',
    sortable: true,
  },
  {
    name: 'labels',
    label: 'labels',
    field: 'labels',
    align: 'left',
    sortable: false,
  },
];

function Goto(row: C2Server) {
  $router.push({ name: 'server', params: { id: row.id } });
}

function status_to_icon(status: string){
  if(status === 'running'){
    return 'done'
  }
  if (status === 'exited') {
    return 'close'
  }
  if (status === 'restarting') {
    return 'hourglass'
  }
  if (status === 'restarted') {
    return 'hourglass'
  }
  if (status === 'deleting') {
    return 'delete'
  }
  return 'question_mark'
}

function run_command(c2_server_id: string, name: string, command: string) {
  loading.value = true;
  api.post(`/c2_servers/${c2_server_id}/command`, { name: name, command: command }).then(() => {
    $q.notify({
      color: 'green-4',
      textColor: 'white',
      message: `${command} success for ${name ? name : c2_server_id}`,
      position: 'top',
    });
    store.LoadData();
  }).catch(() => {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: `${command} failed for ${name ? name : c2_server_id}`,
      icon: 'report_problem',
    });
    store.LoadData();
  })
}

</script>
