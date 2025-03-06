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
    <q-btn color="secondary" icon="refresh" @click="loadData">Refresh</q-btn>
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Share Files" :rows="data" row-key="id"
      :columns="columns" :loading="loading" v-model:pagination="pagination" @request="onRequest"
      :visible-columns="visible">
      <template v-slot:top>
        <div class="col-2 q-table__title">ShareFile</div>
        <q-space />
        <filter-view object-type="share_files" v-model="filters" v-on:updateFilters="updateFilters" />
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
          <q-td key="type" :props="props">
            {{ props.row.type }}
          </q-td>
          <q-td key="unc_path" :props="props">
            {{ props.row.unc_path }}
          </q-td>
          <q-td key="file_id" :props="props">
            {{ props.row.file_id }}
          </q-td>
          <q-td key="parent_id" :props="props">
            {{ props.row.parent_id }}
          </q-td>
          <q-td key="share_id" :props="props">
            {{ props.row.share_id }}
          </q-td>
          <q-td key="size" :props="props">
            {{ prettyBytes(props.row.size) }}
            <q-tooltip>
              {{ props.row.size }}
            </q-tooltip>
          </q-td>
          <q-td key="time_created" :props="props">
            {{ props.row.time_created }}
          </q-td>
          <q-td key="last_accessed" :props="props">
            {{ props.row.last_accessed }}
          </q-td>
          <q-td key="last_modified" :props="props">
            {{ props.row.last_modified }}
          </q-td>
          <q-td key="created" :props="props">
            {{ props.row.created }}
          </q-td>
          <q-td key="depth" :props="props">
            {{ props.row.depth }}
          </q-td>
          <q-td key="name" :props="props">
            {{ props.row.name }}
          </q-td>
          <q-td key="extension" :props="props">
            {{ props.row.extension }}
          </q-td>
          <q-td key="downloaded" :props="props">
            {{ props.row.downloaded }}
          </q-td>
          <q-td key="indexed" :props="props">
            {{ props.row.indexed }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="share_file" :object-id="String(props.row.id)" v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { toRefs, ref, toRaw } from 'vue';
import { ShareFile } from 'src/models';
import useloadData from 'src/load-data';
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import prettyBytes from 'pretty-bytes';
import FilterView from '../components/FilterView.vue';

const props = defineProps({
  host_id: {
    type: String,
    default: '',
  },
  share_id: {
    type: String,
    default: '',
  }
});

const visible = ref(['type', 'unc_path', 'size', 'depth', 'name', 'downloaded', 'indexed', 'labels'])

const { host_id, share_id } = toRefs(props);

const { loading, data, pagination, loadData, onRequest, AddFilter } =
  useloadData<Array<ShareFile>>('share_files');

if (host_id.value) {
  AddFilter({ host_id: host_id.value });
}
if (share_id.value) {
  AddFilter({ share_id: share_id.value });
}

const filters = ref({});

function updateFilters() {
  AddFilter(toRaw(filters.value));
  loadData();
}

loadData();

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: false },
  { name: 'type', label: 'type', field: 'type', align: 'left', sortable: false },
  { name: 'unc_path', label: 'unc_path', field: 'unc_path', align: 'left', sortable: false },
  { name: 'file_id', label: 'file_id', field: 'file_id', align: 'left', sortable: false },
  { name: 'parent_id', label: 'parent_id', field: 'parent_id', align: 'left', sortable: false },
  { name: 'share_id', label: 'share_id', field: 'share_id', align: 'left', sortable: false },
  { name: 'size', label: 'size', field: 'size', align: 'left', sortable: false },
  { name: 'time_created', label: 'time_created', field: 'time_created', align: 'left', sortable: false },
  { name: 'last_accessed', label: 'last_accessed', field: 'last_accessed', align: 'left', sortable: false },
  { name: 'last_modified', label: 'last_modified', field: 'last_modified', align: 'left', sortable: false },
  { name: 'created', label: 'created', field: 'created', align: 'left', sortable: false },
  { name: 'depth', label: 'depth', field: 'depth', align: 'left', sortable: false },
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: false },
  { name: 'extension', label: 'extension', field: 'extension', align: 'left', sortable: false },
  { name: 'downloaded', label: 'downloaded', field: 'downloaded', align: 'left', sortable: false },
  { name: 'indexed', label: 'indexed', field: 'indexed', align: 'left', sortable: false },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

</script>
