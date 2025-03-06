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
      <q-btn color="secondary" icon="add_circle" to="situational_awareness/add">Add entry</q-btn>
      <q-btn color="secondary" icon="refresh" @click="store.LoadData()">Refresh</q-btn>
    </div>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Situational Awareness" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="store.onRequest">
      <template v-slot:top>
        <div class="col-2 q-table__title">Situational Awareness</div>
        <q-space />
        <filter-view object-type="situational_awareness" v-model="filters" v-on:updateFilters="store.updateFilters" />
      </template>
      <template v-slot:body="props">
        <q-tr :props="props" class="cursor-pointer">
          <q-td key="category" :props="props" @click="Click(props.row)">
            {{ props.row.category }}
          </q-td>
          <q-td key="name" :props="props" @click="Click(props.row)">
            {{ props.row.name }}
          </q-td>
          <q-td key="value" :props="props" @click="Click(props.row)">
            {{ FormatValue(props.row) }}
          </q-td>
          <q-td key="domain" :props="props" @click="Click(props.row)">
            <template v-if="props.row.domain_id">
              <template v-if="props.row.domain && props.row.domain.long_name">
                {{ props.row.domain.long_name }}
              </template>
              <template v-else>
                {{ props.row.domain.short_name }}
              </template>
            </template>
          </q-td>
          <q-td key="actions" :props="props">
            <q-btn color="secondary" icon="delete" flat @click="onDelete(props.row)">
              Delete
            </q-btn>
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar, copyToClipboard } from 'quasar';
import { SituationalAwareness } from '../models';
import { QTableProps } from 'quasar';
import { api } from 'src/boot/axios';
import FilterView from '../components/FilterView.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const useStore = defineTypedStore<SituationalAwareness>('situational_awareness');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const $q = useQuasar();

const columns: QTableProps['columns'] = [
  { name: 'category', label: 'category', field: 'category', align: 'left', sortable: true },
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true },
  { name: 'value', label: 'value', field: 'value', align: 'left', sortable: true },
  { name: 'domain', label: 'domain', field: 'domain', align: 'left', sortable: true },
  { name: 'actions', label: 'actions', field: 'actions', align: 'left', sortable: true },
];


function FormatValue(row: SituationalAwareness) {
  if (row.value_string !== null) {
    return row.value_string
  } else if (row.value_int !== null) {
    return row.value_int
  } else if (row.value_bool !== null) {
    return row.value_bool
  } else if (row.value_json !== null) {
    return row.value_json
  }
  return ''
}

function Click(row: SituationalAwareness) {
  copyToClipboard(String(FormatValue(row)))
    .then(() => {
      // success!
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        message: 'Value copied to clipboard!',
        position: 'top',
      });
    })
    .catch(() => {
      // fail
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Failed to copy value to clipboard',
        icon: 'report_problem',
      });
    });
}

function onDelete(row: SituationalAwareness) {
  $q.dialog({
    title: 'Confirm',
    message: 'Do you really want to delete this?',
    cancel: true,
    persistent: true
  }).onOk(() => {
    loading.value = true;
    api
      .delete(`/situational_awareness/${row.id}`)
      .then(() => {
        loading.value = false;
        $q.notify({
          color: 'green-4',
          textColor: 'white',
          icon: 'cloud_done',
          message: `Deleted entry ${row.id}`,
          position: 'top',
        });
        store.LoadData();
      })
      .catch(() => {
        loading.value = false;
        $q.notify({
          color: 'negative',
          position: 'top',
          message: 'Deleting failed',
          icon: 'report_problem',
        });
      });
  })

}

// function Save(row: Domain) {
//   setTimeout(function () {
//     api.put(`/domains/${row.id}`, { long_name: row.long_name, short_name: row.short_name }).then(() => {
//       $q.notify({
//         color: 'green-4',
//         textColor: 'white',
//         icon: 'cloud_done',
//         position: 'top',
//         message: 'Updated domain',
//       });
//     }).catch(() => {
//       $q.notify({
//         color: 'negative',
//         position: 'top',
//         message: 'Error updating domain',
//         icon: 'report_problem',
//       });
//     });
//   }, 100);
// }
</script>
