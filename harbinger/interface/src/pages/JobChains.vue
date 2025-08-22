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
      <q-btn color="secondary" icon="refresh" @click="store.LoadData()">Refresh</q-btn>
      <q-btn color="secondary" icon="add_circle" to="playbooks/add">Add</q-btn>
      <q-btn color="secondary" icon="add_circle" to="playbooks/add_from_template">
        Create from template
      </q-btn>
      <q-btn color="secondary" icon="add_circle" to="playbooks/add_template">
        Create new template
      </q-btn>
      <q-btn color="secondary" icon="fas fa-robot" to="playbooks/add_template_ai">
        Create new template with ai
      </q-btn>
    </div>
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Playbooks" :rows="data" row-key="id"
      :columns="columns" :loading="loading" v-model:pagination="pagination" @request="store.onRequest"
      :visible-columns="visible" selection="multiple" v-model:selected="selected">
      <template v-slot:top>
        <div class="row items-center" style="width: 100%;">
          <div class="col-auto q-table__title" v-if="selected.length === 0">Playbooks</div>
          <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
            <bulk-label-actions :selected="selected" object-type="playbook" @update="selected = []; store.LoadData()" />
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
          <filter-view v-if="selected.length === 0" object-type="playbooks" v-model="filters"
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
          <q-td key="playbook_name" :props="props" @click="Goto(props.row)">
            {{ props.row.playbook_name }}
          </q-td>
          <q-td key="description" :props="props" @click="Goto(props.row)">
            {{ props.row.description }}
          </q-td>
          <q-td key="status" :props="props" @click="Goto(props.row)">
            {{ props.row.status }}
          </q-td>
          <q-td key="steps" :props="props" @click="Goto(props.row)">
            {{ props.row.steps }}
          </q-td>
          <q-td key="completed" :props="props" @click="Goto(props.row)">
            {{ props.row.completed }}
          </q-td>
          <q-td key="playbook_template_id" :props="props" @click="Goto(props.row)">
            {{ props.row.playbook_template_id }}
          </q-td>
          <q-td key="time_created" :props="props" @click="Goto(props.row)">
            {{ props.row.time_created }}
          </q-td>
          <q-td key="time_updated" :props="props" @click="Goto(props.row)">
            {{ props.row.time_updated }}
          </q-td>
          <q-td key="time_started" :props="props" @click="Goto(props.row)">
            {{ props.row.time_started }}
          </q-td>
          <q-td key="time_completed" :props="props" @click="Goto(props.row)">
            {{ props.row.time_completed }}
          </q-td>
          <q-td key="labels" :props="props" @click="Goto(props.row)">
            <labels-list object-type="playbook" :object-id="String(props.row.id)" v-model="props.row.labels" />
          </q-td>
          <q-menu context-menu touch-position>
            <q-list style="min-width: 100px">
              <q-item clickable v-close-popup @click="Goto(props.row)">
                <q-item-section avatar>
                  <q-icon color="secondary" name="open_in_new" />
                </q-item-section>
                <q-item-section>Go to playbook</q-item-section>
              </q-item>

              <q-item clickable v-close-popup @click="Clone(props.row)">
                <q-item-section avatar>
                  <q-icon color="secondary" name="file_copy" />
                </q-item-section>
                <q-item-section>Clone playbook</q-item-section>
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
import { Chain } from '../models';
import { useQuasar } from 'quasar';
import { api } from 'boot/axios';
import { useCounterStore } from 'src/stores/object-counters';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia';
import BulkLabelActions from 'src/components/BulkLabelActions.vue';

const counter_store = useCounterStore();
const selected = ref([]);

counter_store.clear('playbooks');

const visible = ref(['playbook_name', 'description', 'status', 'steps', 'completed', 'labels'])

const useStore = defineTypedStore<Chain>('playbooks');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const $router = useRouter();
const $q = useQuasar();

function Goto(row: Chain) {
  $router.push({ name: 'playbook', params: { id: row.id } });
}

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: false },
  { name: 'playbook_name', label: 'playbook_name', field: 'playbook_name', align: 'left', sortable: false },
  { name: 'description', label: 'description', field: 'description', align: 'left', sortable: false },
  { name: 'status', label: 'status', field: 'status', align: 'left', sortable: false },
  { name: 'steps', label: 'steps', field: 'steps', align: 'left', sortable: false },
  { name: 'completed', label: 'completed', field: 'completed', align: 'left', sortable: false },
  { name: 'playbook_template_id', label: 'playbook_template_id', field: 'playbook_template_id', align: 'left', sortable: false },
  { name: 'time_created', label: 'time_created', field: 'time_created', align: 'left', sortable: false },
  { name: 'time_updated', label: 'time_updated', field: 'time_updated', align: 'left', sortable: false },
  { name: 'time_started', label: 'time_started', field: 'time_started', align: 'left', sortable: false },
  { name: 'time_completed', label: 'time_completed', field: 'time_completed', align: 'left', sortable: false },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

function Clone(row: Chain) {
  api
    .post(`/playbooks/${row.id}/clone`)
    .then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        position: 'top',
        icon: 'cloud_done',
        message: 'Cloned playbook',
      });
      loading.value = false;
      store.LoadData()
    })
    .catch((error) => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: `Failed to clone: ${error.response.data.error}`,
        icon: 'report_problem',
      });
    });
}

function start(row: Chain) {
  api
    .post(`/playbooks/${row.id}/start`)
    .then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: 'Started playbook',
        position: 'top',
      });
      loading.value = false;
      store.LoadData();
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
