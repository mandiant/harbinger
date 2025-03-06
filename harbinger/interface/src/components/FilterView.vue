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
  <div class="row inline q-pa-md">
    <div class="col" v-for="filter, index in filters" v-bind:key="index">
      <filter-select v-model="models[filter.query_name]" v-if="filter.type === 'options'" :multiple="filter.multiple"
        :name="filter.name" :options="filter.options" />
      <q-toggle v-model="models[filter.query_name]" v-if="filter.type === 'bool'" :label="filter.name" />
    </div>
    <div class="col-grow">
      <q-input borderless dense v-model="models['search']" debounce="300" placeholder="Search" autofocus>
        <template v-slot:append>
          <q-icon name="search" />
        </template>
      </q-input>
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from 'boot/axios';
import { ref, toRaw, toRefs, watch } from 'vue';
import { Filter } from '../models';
import FilterSelect from './FilterSelect.vue';

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  objectType: {
    type: String,
    required: true,
  }
});

const { modelValue, objectType } = toRefs(props);

const emit = defineEmits(['update:modelValue', 'updateFilters']);

interface Map {
  [key: string]: string | undefined
}

const filters = ref<Array<Filter>>([])

const models = ref<Map>({} as Map)

for (const key in modelValue.value) {
  models.value[key] = modelValue.value[key];
}

function loadFilters() {
  var result: Map = {} as Map
  for (const [key, value] of Object.entries(models.value)) {
    if (Array.isArray(value)) {
      if (value.length > 0) {
        result[key] = value.join(',')
      }
    } else if (value !== '') {
      result[key] = toRaw(value);
    }
  }
  api.get(`/${objectType.value}/filters`, { params: { ...result } }).then((response) => {
    filters.value = response.data
  })
}
loadFilters()

// eslint-disable-next-line @typescript-eslint/no-unused-vars
watch(models, async () => {
  var result: Map = {} as Map
  for (const [key, value] of Object.entries(models.value)) {
    if (Array.isArray(value)) {
      result[key] = value.join(',')
    } else {
      result[key] = toRaw(value);
    }
  }
  emit('update:modelValue', result);
  emit('updateFilters');
  loadFilters();
}, { deep: true });

</script>
