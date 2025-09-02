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
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Certificate Templates" :rows="data"
      row-key="id" :columns="columns" :loading="loading" v-model:pagination="pagination" @request="onRequest"
      :visible-columns="visible" selection="multiple" v-model:selected="selected">
      <template v-slot:top>
        <div class="row items-center" style="width: 100%;">
          <div class="col-auto q-table__title" v-if="selected.length === 0">Certificate Templates</div>
          <div v-if="selected.length > 0" class="row items-center q-gutter-sm">
            <bulk-label-actions :selected="selected" object-type="certificate_template" @update="selected = []; loadData()" />
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
          <filter-view v-if="selected.length === 0" object-type="certificate_templates" v-model="filters"
            @updateFilters="updateFilters" class="full-width" />
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
          <q-td key="id" :props="props">
            {{ props.row.id }}
          </q-td>
          <q-td key="template_name" :props="props">
            {{ props.row.template_name }}
          </q-td>
          <q-td key="display_name" :props="props">
            {{ props.row.display_name }}
          </q-td>
          <q-td key="enabled" :props="props">
            {{ props.row.enabled }}
          </q-td>
          <q-td key="client_authentication" :props="props">
            {{ props.row.client_authentication }}
          </q-td>
          <q-td key="enrollment_agent" :props="props">
            {{ props.row.enrollment_agent }}
          </q-td>
          <q-td key="any_purpose" :props="props">
            {{ props.row.any_purpose }}
          </q-td>
          <q-td key="enrollee_supplies_subject" :props="props">
            {{ props.row.enrollee_supplies_subject }}
          </q-td>
          <q-td key="requires_manager_approval" :props="props">
            {{ props.row.requires_manager_approval }}
          </q-td>
          <q-td key="requires_manager_archival" :props="props">
            {{ props.row.requires_manager_archival }}
          </q-td>
          <q-td key="authorized_signatures_required" :props="props">
            {{ props.row.authorized_signatures_required }}
          </q-td>
          <q-td key="validity_period" :props="props">
            {{ props.row.validity_period }}
          </q-td>
          <q-td key="renewal_period" :props="props">
            {{ props.row.renewal_period }}
          </q-td>
          <q-td key="minimum_rsa_key_length" :props="props">
            {{ props.row.minimum_rsa_key_length }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="certificate_templates" :object-id="String(props.row.id)"
              v-model="props.row.labels" />
          </q-td>
        </q-tr>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import { ref, toRaw } from 'vue';
import useloadData from 'src/load-data';
import { CertificateTemplate } from 'src/models'
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { useCounterStore } from 'src/stores/object-counters';
import BulkLabelActions from './BulkLabelActions.vue';

const store = useCounterStore();
const selected = ref([]);

store.clear('certificate_templates');

const visible = ref(['template_name', 'display_name', 'enabled', 'client_authentication', 'enrollment_agent', 'any_purpose', 'enrollee_supplies_subject', 'requires_manager_approval', 'authorized_signatures_required', 'labels'])

const { loading, data, pagination, loadData, onRequest, AddFilter } =
  useloadData<Array<CertificateTemplate>>('certificate_templates');

const filters = ref({});

function updateFilters() {
  AddFilter(toRaw(filters.value));
  loadData();
}

loadData()

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: false },
  { name: 'template_name', label: 'template_name', field: 'template_name', align: 'left', sortable: false },
  { name: 'display_name', label: 'display_name', field: 'display_name', align: 'left', sortable: false },
  { name: 'enabled', label: 'enabled', field: 'enabled', align: 'left', sortable: false },
  { name: 'client_authentication', label: 'client_authentication', field: 'client_authentication', align: 'left', sortable: false },
  { name: 'enrollment_agent', label: 'enrollment_agent', field: 'enrollment_agent', align: 'left', sortable: false },
  { name: 'any_purpose', label: 'any_purpose', field: 'any_purpose', align: 'left', sortable: false },
  { name: 'enrollee_supplies_subject', label: 'enrollee_supplies_subject', field: 'enrollee_supplies_subject', align: 'left', sortable: false },
  { name: 'requires_manager_approval', label: 'requires_manager_approval', field: 'requires_manager_approval', align: 'left', sortable: false },
  { name: 'requires_manager_archival', label: 'requires_manager_archival', field: 'requires_manager_archival', align: 'left', sortable: false },
  { name: 'authorized_signatures_required', label: 'authorized_signatures_required', field: 'authorized_signatures_required', align: 'left', sortable: false },
  { name: 'validity_period', label: 'validity_period', field: 'validity_period', align: 'left', sortable: false },
  { name: 'renewal_period', label: 'renewal_period', field: 'renewal_period', align: 'left', sortable: false },
  { name: 'minimum_rsa_key_length', label: 'minimum_rsa_key_length', field: 'minimum_rsa_key_length', align: 'left', sortable: false },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

</script>