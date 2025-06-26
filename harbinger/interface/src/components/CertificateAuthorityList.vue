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
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Certificate Authorities" :rows="data"
      row-key="id" :columns="columns" :loading="loading" v-model:pagination="pagination" @request="onRequest"
      :visible-columns="visible">
      <template v-slot:top> 
        <div class="row items-center" style="width: 100%;">
          <div class="col-auto q-table__title">Certificate Authorities</div>
          <q-space />
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
        </div>
        <div class="row" style="width: 100%;">
          <filter-view object-type="certificate_authorities" v-model="filters" @updateFilters="updateFilters"
            class="full-width" />
        </div>
      </template>
      <template v-slot:body="props">
        <q-tr :props="props" class="cursor-pointer">
          <q-td key="id" :props="props">
            {{ props.row.id }}
          </q-td>
          <q-td key="ca_name" :props="props">
            {{ props.row.ca_name }}
          </q-td>
          <q-td key="dns_name" :props="props">
            {{ props.row.dns_name }}
          </q-td>
          <q-td key="certificate_subject" :props="props">
            {{ props.row.certificate_subject }}
          </q-td>
          <q-td key="certificate_serial_number" :props="props">
            {{ props.row.certificate_serial_number }}
          </q-td>
          <q-td key="certificate_validity_start" :props="props">
            {{ props.row.certificate_validity_start }}
          </q-td>
          <q-td key="certificate_validity_end" :props="props">
            {{ props.row.certificate_validity_end }}
          </q-td>
          <q-td key="web_enrollment" :props="props">
            {{ props.row.web_enrollment }}
          </q-td>
          <q-td key="user_specified_san" :props="props">
            {{ props.row.user_specified_san }}
          </q-td>
          <q-td key="request_disposition" :props="props">
            {{ props.row.request_disposition }}
          </q-td>
          <q-td key="enforce_encryption_for_requests" :props="props">
            {{ props.row.enforce_encryption_for_requests }}
          </q-td>

          <q-td key="labels" :props="props">
            <labels-list object-type="certificate_authority" :object-id="String(props.row.id)"
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
import { CertificateAuthority } from 'src/models'
import { QTableProps } from 'quasar';
import LabelsList from './LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { useCounterStore } from 'src/stores/object-counters';

const store = useCounterStore();

store.clear('certificate_authorities');

const visible = ref(['ca_name', 'dns_name', 'certificate_subject', 'web_enrollment', 'user_specified_san', 'request_disposition', 'enforce_encryption_for_requests', 'labels'])

const { loading, data, pagination, loadData, onRequest, AddFilter } =
  useloadData<Array<CertificateAuthority>>('certificate_authorities');

const filters = ref({});

function updateFilters() {
  AddFilter(toRaw(filters.value));
  loadData();
}

loadData()

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: false },
  { name: 'ca_name', label: 'ca_name', field: 'ca_name', align: 'left', sortable: false },
  { name: 'dns_name', label: 'dns_name', field: 'dns_name', align: 'left', sortable: false },
  { name: 'certificate_subject', label: 'certificate_subject', field: 'certificate_subject', align: 'left', sortable: false },
  { name: 'certificate_serial_number', label: 'certificate_serial_number', field: 'certificate_serial_number', align: 'left', sortable: false },
  { name: 'certificate_validity_start', label: 'certificate_validity_start', field: 'certificate_validity_start', align: 'left', sortable: false },
  { name: 'certificate_validity_end', label: 'certificate_validity_end', field: 'certificate_validity_end', align: 'left', sortable: false },
  { name: 'web_enrollment', label: 'web_enrollment', field: 'web_enrollment', align: 'left', sortable: false },
  { name: 'user_specified_san', label: 'user_specified_san', field: 'user_specified_san', align: 'left', sortable: false },
  { name: 'request_disposition', label: 'request_disposition', field: 'request_disposition', align: 'left', sortable: false },
  { name: 'enforce_encryption_for_requests', label: 'enforce_encryption_for_requests', field: 'enforce_encryption_for_requests', align: 'left', sortable: false },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];

</script>