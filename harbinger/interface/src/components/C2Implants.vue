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
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Implants" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="store.onRequest" :visible-columns="visible" selection="multiple" v-model:selected="selected">
      <template v-slot:top>
        <div class="row items-center" style="width: 100%;">
          <div class="col-auto q-table__title" v-if="selected.length === 0">Implants</div>
          <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
            <bulk-label-actions :selected="selected" object-type="c2_implant" @update="selected = []; store.LoadData()" />
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
          <filter-view v-if="selected.length === 0" object-type="c2_implants" v-model="filters"
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
          <q-td key="c2_type" :props="props" @click="Goto(props.row)">
            {{ props.row.c2_type }}
          </q-td>
          <q-td key="payload_type" :props="props" @click="Goto(props.row)">
            {{ props.row.payload_type }}
          </q-td>
          <q-td key="ip" :props="props" @click="Goto(props.row)">
            {{ props.row.ip }}
          </q-td>
          <q-td key="last_checkin_formatted" :props="props" @click="Goto(props.row)">
            {{ timeDiffs.get(props.row.id) }}
          </q-td>
          <q-td key="hostname" :props="props" @click="Goto(props.row)">
            {{ props.row.hostname }}
          </q-td>
          <q-td key="username" :props="props" @click="Goto(props.row)">
            {{ props.row.username }}
          </q-td>
          <q-td key="domain" :props="props" @click="Goto(props.row)">
            {{ props.row.domain }}
          </q-td>
          <q-td key="description" :props="props" @click="Goto(props.row)">
            {{ props.row.description }}
          </q-td>
          <q-td key="sleep" :props="props" @click="Goto(props.row)">
            {{ props.row.sleep }}
          </q-td>
          <q-td key="jitter" :props="props" @click="Goto(props.row)">
            {{ props.row.jitter }}
          </q-td>
          <q-td key="os" :props="props" @click="Goto(props.row)">
            {{ props.row.os }}
          </q-td>
          <q-td key="pid" :props="props" @click="Goto(props.row)">
            {{ props.row.pid }}
          </q-td>
          <q-td key="architecture" :props="props" @click="Goto(props.row)">
            {{ props.row.architecture }}
          </q-td>
          <q-td key="process" :props="props" @click="Goto(props.row)">
            {{ props.row.process }}
          </q-td>
          <q-td key="external_ip" :props="props" @click="Goto(props.row)">
            {{ props.row.external_ip }}
          </q-td>
          <q-td key="last_checkin" :props="props" @click="Goto(props.row)">
            {{ props.row.last_checkin }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="c2_implant" :object-id="String(props.row.id)" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { toRefs, ref, computed, onMounted, onUnmounted } from 'vue';
import { date } from 'quasar';
import { C2Implant } from 'src/models';
import { useRouter } from 'vue-router';
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import { useCounterStore } from 'src/stores/object-counters';
import FilterView from '../components/FilterView.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia';
import BulkLabelActions from './BulkLabelActions.vue';

const useStore = defineTypedStore<C2Implant>('c2_implants');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
const selected = ref([]);

const counter_store = useCounterStore();
counter_store.clear('c2_implants');

const props = defineProps({
  host_id: {
    type: String,
    default: '',
  },
  c2_server_id: {
    type: String,
    default: '',
  }
});

const $router = useRouter();

const { host_id, c2_server_id } = toRefs(props);

if (host_id.value) {
  store.AddFilter({ host_id: host_id.value });
} else {
  store.RemoveFilter('host_id');
}
if (c2_server_id.value) {
  store.AddFilter({ c2_server_id: c2_server_id.value });
} else {
  store.RemoveFilter('c2_server_id');
}
store.LoadData();

const visible = ref(['c2_type', 'payload_type', 'ip', 'last_checkin_formatted', 'hostname', 'username', 'pid', 'architecture', 'process', 'external_ip', 'labels'])

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  { name: 'c2_type', label: 'c2_type', field: 'c2_type', align: 'left', sortable: true },
  { name: 'payload_type', label: 'payload_type', field: 'payload_type', align: 'left', sortable: true },
  { name: 'ip', label: 'ip', field: 'ip', align: 'left', sortable: true },
  { name: 'last_checkin_formatted', label: 'last_checkin_formatted', field: 'last_checkin_formatted', align: 'left', sortable: true },
  { name: 'hostname', label: 'hostname', field: 'hostname', align: 'left', sortable: true },
  { name: 'username', label: 'username', field: 'username', align: 'left', sortable: true },
  { name: 'domain', label: 'domain', field: 'domain', align: 'left', sortable: true },
  { name: 'description', label: 'description', field: 'description', align: 'left', sortable: true },
  { name: 'sleep', label: 'sleep', field: 'sleep', align: 'left', sortable: true },
  { name: 'jitter', label: 'jitter', field: 'jitter', align: 'left', sortable: true },
  { name: 'os', label: 'os', field: 'os', align: 'left', sortable: true },
  { name: 'pid', label: 'pid', field: 'pid', align: 'left', sortable: true },
  { name: 'architecture', label: 'architecture', field: 'architecture', align: 'left', sortable: true },
  { name: 'process', label: 'process', field: 'process', align: 'left', sortable: true },
  { name: 'external_ip', label: 'external_ip', field: 'external_ip', align: 'left', sortable: true },
  { name: 'last_checkin', label: 'last_checkin', field: 'last_checkin', align: 'left', sortable: true },
  {
    name: 'labels',
    label: 'labels',
    field: 'labels',
    align: 'left',
    sortable: true,
  },
];

const nonPaddedIntl = Intl.NumberFormat('en-gb', {
  minimumIntegerDigits: 1,
});
const paddedIntl = Intl.NumberFormat('en-gb', { minimumIntegerDigits: 2 });

const now = ref(Date.now());

function formatDate(last_checkin: string) {
  const last_checkin_date = Date.parse(last_checkin);
  const duration = date.getDateDiff(now.value, last_checkin_date, 'seconds');
  const days = Math.floor(duration / 3600 / 24);
  if ((days) > 1) {
    return `${days}d`
  }
  const hours = Math.floor(duration / 3600);
  const minutes = Math.floor(duration / 60) % 60;
  const seconds = duration % 60;
  const indexToPad = hours ? 0 : 1;
  const timeFormat = [hours, minutes, seconds]
    .map((val, i) => {
      return val < 10 && i > indexToPad
        ? paddedIntl.format(val)
        : nonPaddedIntl.format(val);
    })
    .filter((val, i) => {
      if (i === 0) {
        return !(val === '00' || val === '0');
      }

      return true;
    })
    .join(':'); // 4:32
  return timeFormat;
}

function Goto(row: C2Implant) {
  $router.push({ name: 'implant', params: { id: row.id } });
}

const timeDiffs = computed(() => {
  const diffs = new Map<string, string>();
  data.value.forEach((item) => {
    diffs.set(item.id, formatDate(item.last_checkin))
  });
  return diffs;
});

let timer: NodeJS.Timeout;
onMounted(() => {
  timer = setInterval(() => {
    now.value = Date.now()
  }, 1000);
});

onUnmounted(() => {
  clearInterval(timer);
});

</script>
