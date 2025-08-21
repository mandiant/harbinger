<template>
<div>
    <div class="row q-gutter-sm">
      <q-btn color="secondary" icon="add_circle" to="plans/add">Add plan</q-btn>
      <q-btn color="secondary" icon="refresh" @click="store.LoadData">Refresh</q-btn>
    </div>
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Plan" :rows="data" row-key="id"
    :columns="columns" :loading="loading" v-model:pagination="pagination" @request="store.onRequest"
    :visible-columns="visible">
    <template v-slot:top>
        <div class="col-2 q-table__title">Plan</div>
        <q-space />
        <filter-view object-type="plans" v-model="filters" v-on:updateFilters="store.updateFilters" />
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
        <q-tr :props="props" class="cursor-pointer" @click="goToPlan(props.row.id)">
        <q-td key="id" :props="props">
            {{ props.row.id }}
        </q-td>
        <q-td key="name" :props="props">
            {{ props.row.name }}
        </q-td>
        <q-td key="description" :props="props">
            {{ props.row.description }}
        </q-td>
        <q-td key="graph" :props="props">
            {{ props.row.graph }}
        </q-td>
        <q-td key="correct" :props="props">
            {{ props.row.correct }}
        </q-td>
        <q-td key="status" :props="props">
            {{ props.row.status }}
        </q-td>
        <q-td key="llm_status" :props="props">
            {{ props.row.llm_status }}
        </q-td>
        <q-td key="time_created" :props="props">
            {{ props.row.time_created }}
        </q-td>
        <q-td key="time_updated" :props="props">
            {{ props.row.time_updated }}
        </q-td>
        
        <q-td key="labels" :props="props">
            <labels-list object-type="plans" :object-id="String(props.row.id)" v-model="props.row.labels" />
        </q-td>
        </q-tr>
    </template>
    <template v-slot:no-data>
        <div class="full-width row flex-center text-accent q-gutter-sm">
            <q-icon size="2em" name="sentiment_dissatisfied" />
            <span>
                No plans found.
            </span>
        </div>
    </template>
    <template v-slot:loading>
        <q-inner-loading showing color="primary" />
    </template>
    </q-table>
</div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Plan } from 'src/models'
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { useCounterStore } from 'src/stores/object-counters';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'
import { useRouter } from 'vue-router';

const router = useRouter();

function goToPlan(id: string) {
  router.push({ name: 'plan', params: { id } });
}

const counter_store = useCounterStore();

counter_store.clear('plans');
const visible = ref(['name', 'objective', 'status', 'llm_status'])

const useStore = defineTypedStore<Plan>('plans');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const columns: QTableProps['columns'] = [
{ name: 'id', label: 'id', field: 'id', align: 'left', sortable: false },
{ name: 'name', label: 'name', field: 'name', align: 'left', sortable: false },
{ name: 'description', label: 'description', field: 'description', align: 'left', sortable: false },
{ name: 'graph', label: 'graph', field: 'graph', align: 'left', sortable: false },
{ name: 'correct', label: 'correct', field: 'correct', align: 'left', sortable: false },
{ name: 'status', label: 'status', field: 'status', align: 'left', sortable: false },
{ name: 'llm_status', label: 'llm_status', field: 'llm_status', align: 'left', sortable: false },
{ name: 'time_created', label: 'time_created', field: 'time_created', align: 'left', sortable: false },
{ name: 'time_updated', label: 'time_updated', field: 'time_updated', align: 'left', sortable: false },
{ name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

</script>