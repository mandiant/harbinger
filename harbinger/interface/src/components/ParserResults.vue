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
  <q-card-section>
    <q-timeline color="secondary">
      <q-timeline-entry heading>Parser results</q-timeline-entry>
      <q-timeline-entry
        :title="entry.parser"
        :subtitle="entry.time_created"
        v-for="entry in data"
        v-bind:key="entry.id"
        color="green"
      >
        <q-input v-model="entry.log" readonly autogrow  />
      </q-timeline-entry>
      <q-inner-loading :showing="loading">
        <q-spinner-gears size="50px" color="secondary" />
      </q-inner-loading>
    </q-timeline>
  </q-card-section>
  <q-card-actions>
    <q-pagination
      v-model="current"
      direction-links
      :max="pages"
      flat
      color="grey"
      active-color="primary"
    />
  </q-card-actions>
</template>

<script setup lang="ts">
import { toRefs, watch, computed, ref } from 'vue';
import useloadData from 'src/load-data';
import { ParseResult } from '../models'

const props = defineProps({
  file_id: {
    type: String,
    default: '',
  },
});

const { file_id } = toRefs(props);

const { loading, data, pagination, loadData, AddFilter } = useloadData<
  Array<ParseResult>
>('parse_results');
if (file_id.value) {
  AddFilter({ file_id: file_id.value });
  loadData();
}
const current = ref(1);
watch(current, (old_value, new_value) => {
  if (old_value !== new_value) {
    pagination.value.page = current.value;
    loadData();
  }
});

const pages = computed(() =>
  Math.ceil(pagination.value.rowsNumber / pagination.value.rowsPerPage)
);
</script>
