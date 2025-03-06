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
    <q-btn color="secondary" icon="add_circle" to="objectives/add">Add objective</q-btn>
    <q-btn color="secondary" icon="refresh" @click="store.LoadData">Refresh</q-btn>
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Objectives" :rows="data" row-key="id"
    :columns="columns" :loading="loading" v-model:pagination="pagination" @request="store.onRequest"
    :visible-columns="visible">
    <template v-slot:top>
        <div class="col-2 q-table__title">Objectives</div>
        <q-space />
        <filter-view object-type="objectives" v-model="filters" v-on:updateFilters="store.updateFilters" />
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
            {{ props.row.status }}
        </q-td>
        <q-td key="time_created" :props="props">
            {{ props.row.time_created }}
        </q-td>
        <q-td key="time_updated" :props="props">
            {{ props.row.time_updated }}
        </q-td>
        
        <q-td key="labels" :props="props">
            <labels-list object-type="objectives" :object-id="String(props.row.id)" v-model="props.row.labels" />
        </q-td>
        </q-tr>
    </template>
    </q-table>
</div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Objective } from 'src/models'
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { useCounterStore } from 'src/stores/object-counters';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const counter_store = useCounterStore();

counter_store.clear('objectives');
const visible = ref(['name', 'description', 'status', 'time_created', 'time_updated'])

const useStore = defineTypedStore<Objective>('objectives');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const columns: QTableProps['columns'] = [
{ name: 'id', label: 'id', field: 'id', align: 'left', sortable: false },
{ name: 'name', label: 'name', field: 'name', align: 'left', sortable: false },
{ name: 'description', label: 'description', field: 'description', align: 'left', sortable: false },
{ name: 'status', label: 'status', field: 'status', align: 'left', sortable: false },
{ name: 'time_created', label: 'time_created', field: 'time_created', align: 'left', sortable: false },
{ name: 'time_updated', label: 'time_updated', field: 'time_updated', align: 'left', sortable: false },
{ name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

</script>