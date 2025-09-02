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
    <div class="row q-gutter-sm">
      <q-btn color="secondary" icon="refresh" @click="fileStore.LoadData()">Refresh</q-btn>
      <q-btn color="secondary" icon="upload_file" to="files/add">
        Upload file
      </q-btn>
      <q-btn color="secondary" icon="upload_file" to="files/add_multiple">
        Upload files
      </q-btn>
      <q-btn color="secondary" icon="download" @click="exportFiles()" :loading="exportLoading">Export</q-btn>
      <q-btn color="secondary" icon="open_in_new" to="highlights">
        Highlights
      </q-btn>
    </div>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Files" :rows="data" row-key="id" :columns="columns" :loading="loading"
      v-model:pagination="pagination" @request="fileStore.onRequest" :visible-columns="visible" selection="multiple" v-model:selected="selected">
      <template v-slot:top="props">
        <div class="col-2 q-table__title" v-if="selected.length === 0">Files</div>

        <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
          <bulk-label-actions :selected="selected" object-type="file" @update="selected = []; fileStore.LoadData()" />
          <q-btn dense icon="clear" @click="selected = []" flat>
            <q-tooltip>Clear Selection</q-tooltip>
          </q-btn>
          <div>{{ selected.length }} item(s) selected</div>
        </div>

        <q-space />

        <filter-view v-if="selected.length === 0" object-type="files" v-model="filters" v-on:updateFilters="fileStore.updateFilters" />
        
        <q-select
          v-if="selected.length === 0"
          v-model="visible"
          multiple
          borderless
          dense
          options-dense
          :display-value="$q.lang.table.columns"
          emit-value
          map-options
          :options="columns"
          option-value="name"
          style="min-width: 150px"
        >
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
          <q-td key="filetype" :props="props">
            {{ props.row.filetype }}
            <q-popup-edit v-model="props.row.filetype" title="Update filetype" buttons v-slot="scope"
              @save="Save(props.row)">
              <q-select :options="file_store.fileTypes" v-model="scope.value" dense autofocus />
            </q-popup-edit>
          </q-td>
          <q-td key="filename" :props="props" @click="Goto(props.row)">
            {{ props.row.filename }}
          </q-td>
          <q-td key="magic_mimetype" :props="props" @click="Goto(props.row)">
            {{ props.row.magic_mimetype }}
          </q-td>
          <q-td key="magika_mimetype" :props="props" @click="Goto(props.row)">
            {{ props.row.magika_mimetype }}
          </q-td>
          <q-td key="exiftool" :props="props" @click="Goto(props.row)">
            <q-btn color="secondary" icon="open_in_new" flat v-if="props.row.exiftool" label="Exiftool output"
              @click="output = props.row.exiftool; showDialog = true" />
          </q-td>
          <q-td key="md5sum" :props="props" @click="Goto(props.row)">
            {{ props.row.md5sum }}
          </q-td>
          <q-td key="sha1sum" :props="props" @click="Goto(props.row)">
            {{ props.row.sha1sum }}
          </q-td>
          <q-td key="sha256sum" :props="props" @click="Goto(props.row)">
            {{ props.row.sha256sum }}
          </q-td>
          <q-td key="job_id" :props="props" @click="Goto(props.row)">
            {{ props.row.job_id }}
          </q-td>
          <q-td key="bucket" :props="props" @click="Goto(props.row)">
            {{ props.row.bucket }}
          </q-td>
          <q-td key="path" :props="props" @click="Goto(props.row)">
            {{ props.row.path }}
          </q-td>
          <q-td key="processing_status" :props="props" @click="Goto(props.row)">
            {{ props.row.processing_status }}
          </q-td>
          <q-td key="processing_progress" :props="props" @click="Goto(props.row)">
            {{ props.row.processing_progress }}
          </q-td>
          <q-td key="processing_note" :props="props" @click="Goto(props.row)">
            {{ props.row.processing_note }}
          </q-td>
          <q-td key="c2_task_id" :props="props" @click="Goto(props.row)">
            {{ props.row.c2_task_id }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="file" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
          <q-menu context-menu touch-position>
            <q-list style="min-width: 100px">
              <q-item clickable v-close-popup @click="Parse(props.row)">
                <q-item-section avatar>
                  <q-icon color="secondary" name="refresh" />
                </q-item-section>
                <q-item-section>Parse</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="Download(props.row)">
                <q-item-section avatar>
                  <q-icon color="secondary" name="download" />
                </q-item-section>
                <q-item-section>Download</q-item-section>
              </q-item>
              <q-item clickable v-close-popup @click="GotoTab(props.row)">
                <q-item-section avatar>
                  <q-icon color="secondary" name="open_in_new" />
                </q-item-section>
                <q-item-section>Open tab</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-tr>
      </template>
    </q-table>
    <q-dialog v-model="showDialog">
      <q-card style="min-width: 50vw; max-width: 50vw;">
        <q-card-section>
          <q-input v-model="output" autogrow type="textarea" readonly />
        </q-card-section>
        <q-card-actions>
          <q-btn color="primary" label="OK" @click="showDialog = false" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, toRaw } from 'vue';
import { api } from 'boot/axios';
import { File } from '../models';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import { useQuasar } from 'quasar';
import { useFileStore } from 'src/stores/files';
import { useRouter } from 'vue-router';
import FilterView from '../components/FilterView.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia';
import BulkLabelActions from './BulkLabelActions.vue';

const selected = ref([]);

// Data store which caches files.
const useFiles = defineTypedStore<File>('files');
const fileStore = useFiles();

// Just for file types for now
const file_store = useFileStore()

const { loading, data, pagination, filters } = storeToRefs(fileStore);

fileStore.Load();

const $q = useQuasar();

const visible = ref(['filetype', 'filename', 'magic_mimetype', 'magika_mimetype', 'labels'])

const showDialog = ref(false);
const output = ref('');

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  { name: 'filetype', label: 'filetype', field: 'filetype', align: 'left', sortable: true },
  { name: 'filename', label: 'filename', field: 'filename', align: 'left', sortable: true },
  { name: 'magic_mimetype', label: 'magic_mimetype', field: 'magic_mimetype', align: 'left', sortable: true },
  { name: 'magika_mimetype', label: 'magika_mimetype', field: 'magika_mimetype', align: 'left', sortable: true },
  { name: 'exiftool', label: 'exiftool', field: 'exiftool', align: 'left', sortable: true },
  { name: 'md5sum', label: 'md5sum', field: 'md5sum', align: 'left', sortable: true },
  { name: 'sha1sum', label: 'sha1sum', field: 'sha1sum', align: 'left', sortable: true },
  { name: 'sha256sum', label: 'sha256sum', field: 'sha256sum', align: 'left', sortable: true },
  { name: 'job_id', label: 'job_id', field: 'job_id', align: 'left', sortable: true },
  { name: 'bucket', label: 'bucket', field: 'bucket', align: 'left', sortable: true },
  { name: 'path', label: 'path', field: 'path', align: 'left', sortable: true },
  { name: 'processing_status', label: 'processing_status', field: 'processing_status', align: 'left', sortable: true },
  { name: 'processing_progress', label: 'processing_progress', field: 'processing_progress', align: 'left', sortable: true },
  { name: 'processing_note', label: 'processing_note', field: 'processing_note', align: 'left', sortable: true },
  { name: 'c2_task_id', label: 'c2_task_id', field: 'c2_task_id', align: 'left', sortable: true },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

function Parse(row: File) {
  api.post(`/files/${row.id}/parse`).then(() => {
    $q.notify({
      color: 'green-4',
      textColor: 'white',
      icon: 'cloud_done',
      position: 'top',
      message: 'Parsing file started',
    });
  }).catch(() => {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: 'Error starting file parsing',
      icon: 'report_problem',
    });
  });
}

function Download(row: File) {
  api.get(`/files/${row.id}/download`, { responseType: 'blob' }).then((response) => {
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', row.filename);
    document.body.appendChild(link);
    link.click();
    $q.notify({
      color: 'green-4',
      textColor: 'white',
      icon: 'cloud_done',
      position: 'top',
      message: 'Downloaded file',
    });
  }).catch(() => {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: 'Error downloading file',
      icon: 'report_problem',
    });
  });
}

function Save(row: File) {
  setTimeout(function () {
    api.put(`/files/${row.id}`, { filetype: row.filetype }).then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        position: 'top',
        message: 'Updated filetype',
      });
    }).catch(() => {
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Error updating filetype',
        icon: 'report_problem',
      });
    });
  }, 100)
}

const exportLoading = ref(false);
interface Map {
  [key: string]: string | undefined | unknown
}
function exportFiles() {
  exportLoading.value = true;
  var result: Map = {} as Map
  for (const [key, value] of Object.entries(filters.value)) {
    if (Array.isArray(value)) {
      if(value.length > 0){
        result[key] = value.join(',')
      }
    } else {
      result[key] = toRaw(value);
    }
  }
  result['max_number'] = 1000000
  api.get('/files/export', { params: { ...result }, responseType: 'blob' }).then((response) => {
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'files.zip');
    document.body.appendChild(link);
    link.click();
    $q.notify({
      color: 'green-4',
      textColor: 'white',
      icon: 'cloud_done',
      position: 'top',
      message: 'Exported files',
    });
    exportLoading.value = false;
  }).catch(() => {
    exportLoading.value = false;
    $q.notify({
      color: 'negative',
      position: 'top',
      message: 'Error exporting files',
      icon: 'report_problem',
    });
  });
}


const $router = useRouter();


function Goto(row: File) {
  $router.push({ name: 'file', params: { id: row.id } });
}

function GotoTab(row: File) {
  const routeData = $router.resolve({ name: 'file', params: { id: row.id } });
  window.open(routeData.href, '_blank');
}

</script>
