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
      <q-btn color="secondary" icon="add_circle" to="credentials/add">Add credential</q-btn>
      <q-btn color="secondary" icon="refresh" @click="store.LoadData()">Refresh</q-btn>
    </div>
    <q-table :rows-per-page-options="[5, 10, 15, 20, 25, 50, 100]" title="Credential" :rows="data" row-key="id"
      :columns="columns" :loading="loading" v-model:pagination="pagination" @request="store.onRequest"
      :visible-columns="visible">
      <template v-slot:top> 
        <div class="row items-center" style="width: 100%;">
          <div class="col-auto q-table__title">Credentials</div>
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
          <filter-view object-type="credentials" v-model="filters" @updateFilters="store.updateFilters"
            class="full-width" />
        </div>
      </template>

      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td key="id" :props="props">
            {{ props.row.id }}
          </q-td>
          <q-td key="domain" :props="props">
            <span v-if="props.row.domain">
              <template v-if="props.row.domain.long_name">
                {{ props.row.domain.long_name }}
              </template>
              <template v-else>
                {{ props.row.domain.short_name }}
              </template>
            </span>
          </q-td>
          <q-td key="username" :props="props">
            {{ props.row.username }}
          </q-td>
          <q-td key="password" :props="props">
            {{ Truncate(formatPassword(props.row.password, props.row.kerberos)) }}
          </q-td>
          <q-td key="note" :props="props">
            {{ props.row.note }}
          </q-td>
          <q-td key="labels" :props="props">
            <labels-list object-type="credential" :object-id="props.row.id" v-model="props.row.labels" />
          </q-td>
        </q-tr>
        <q-menu context-menu touch-position>
          <q-list style="min-width: 100px">
            <q-item @click="MarkOwned(props.row)" clickable v-close-popup>
              <q-item-section avatar>
                <q-icon color="secondary" name="fas fa-skull" />
              </q-item-section>
              <q-item-section>Mark as owned</q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </template>
    </q-table>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import { Password, Credential, Kerberos } from '../models';
import BreadCrumb from '../components/BreadCrumb.vue';
import { useCounterStore } from 'src/stores/object-counters';
import useMark from 'src/mark-owned';
import { QTableProps } from 'quasar';
import LabelsList from '../components/LabelsList.vue';
import FilterView from '../components/FilterView.vue';
import { Truncate } from 'src/truncate';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const counter_store = useCounterStore();

counter_store.clear('credential');

const useStore = defineTypedStore<Credential>('credentials');
const store = useStore();
const { loading, data, pagination, filters } = storeToRefs(store);
store.Load();

const { markOwned } = useMark();

const visible = ref(['id', 'domain', 'username', 'password', 'labels'])

function MarkOwned(row: Credential) {
  let name = '';
  if (row.domain) {
    name = `${row.username}@${row.domain.long_name}`.toUpperCase();
    markOwned(name, store.LoadData);
  }
}

const columns: QTableProps['columns'] = [
  { name: 'id', label: 'id', field: 'id', align: 'left', sortable: true },
  {
    name: 'domain',
    label: 'domain',
    field: (row: Credential) =>
      row.domain !== null ? row.domain.long_name : '',
    align: 'left',
  },
  { name: 'username', label: 'username', field: 'username', align: 'left' },
  {
    name: 'password',
    label: 'password / kerberos',
    field: (row: Credential) => formatPassword(row.password, row.kerberos),
    align: 'left',
  },
  {
    name: 'note',
    label: 'note',
    field: 'note',
    align: 'left',
  },
  { name: 'labels', label: 'labels', field: 'labels', align: 'left', sortable: false },
];


function formatPassword(obj: Password, kerb: Kerberos) {
  if (obj !== null) {
    if (obj.password !== null && obj.password !== '') {
      return obj.password;
    }
    if (obj.nt !== null && obj.nt !== '') {
      return 'ntlm: ' + obj.nt;
    }
    if (obj.aes128_key !== null && obj.aes128_key !== '') {
      return 'aes128: ' + obj.aes128_key;
    }
    if (obj.aes256_key !== null && obj.aes256_key !== '') {
      return 'aes256: ' + obj.aes256_key;
    }
  }
  else if (kerb !== null) {
    return 'kerberos ticket: ' + kerb.client
  }
  return '';
}
</script>
