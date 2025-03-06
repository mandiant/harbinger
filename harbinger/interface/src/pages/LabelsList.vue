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
    <bread-crumb />
    <div class="row q-gutter-sm">
      <q-btn color="secondary" icon="add_circle" to="labels/add">
        Add label
      </q-btn>
      <q-btn color="secondary" icon="refresh" @click="store.LoadData()">Refresh</q-btn>
    </div>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Labels" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="store.onRequest">
      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td key="id" :props="props">
            {{ props.row.id }}
          </q-td>
          <q-td key="preview" :props="props">
            <q-btn flat :label="props.row.name" :style="{ background: props.row.color }"
              :text-color="calcColor(props.row)" />
          </q-td>
          <q-td key="name" :props="props">
            {{ props.row.name }}
          </q-td>
          <q-td key="category" :props="props">
            {{ props.row.category }}
          </q-td>
          <q-td key="color" :props="props">
            {{ props.row.color }}
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import BreadCrumb from '../components/BreadCrumb.vue';
import { Label } from '../models';
import { QTableProps } from 'quasar';
import { useCounterStore } from 'src/stores/object-counters';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const counter_store = useCounterStore();

counter_store.clear('label');

const useStore = defineTypedStore<Label>('labels');
const store = useStore();
const { loading, data, pagination } = storeToRefs(store);
store.Load();

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  { name: 'preview', label: 'preview', field: 'preview', align: 'left', sortable: false },
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true },
  { name: 'category', label: 'category', field: 'category', align: 'left', sortable: true },
  { name: 'color', label: 'color', field: 'color', align: 'left', sortable: true },
]

// from https://stackoverflow.com/a/12043228
function calcColor(label: Label) {
  var c = label.color.substring(1);      // strip #
  var rgb = parseInt(c, 16);   // convert rrggbb to decimal
  var r = (rgb >> 16) & 0xff;  // extract red
  var g = (rgb >> 8) & 0xff;  // extract green
  var b = (rgb >> 0) & 0xff;  // extract blue

  var luma = 0.2126 * r + 0.7152 * g + 0.0722 * b; // per ITU-R BT.709

  if (luma < 80) {
    return 'white'
  }
  return 'black'
}
</script>
