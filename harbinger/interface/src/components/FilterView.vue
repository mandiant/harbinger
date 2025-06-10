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
  <div class="column q-px-md q-py-none q-pb-xs">
    <div class="row q-gutter-sm justify-evenly">
      <div
        :class="filterColClasses"
        v-for="(filter, index) in visibleFilters"
        :key="index"
      >
        <filter-select v-model="models[filter.query_name]" v-if="filter.type === 'options'" :multiple="filter.multiple"
          :name="filter.name" :options="filter.options" />
        <q-toggle v-model="models[filter.query_name]" v-if="filter.type === 'bool'" :label="filter.name" />
      </div>

      <div class="col-xs-12 col-sm-auto">
        <q-input borderless dense v-model="models['search']" debounce="300" placeholder="Search" autofocus>
          <template v-slot:append>
            <q-icon name="search" />
          </template>
        </q-input>
      </div>
    </div>

    <div class="row justify-center q-pt-xs" v-if="filters.length > initialDisplayLimit">
      <q-btn
        flat
        color="primary"
        @click="toggleShowAllFilters"
        :label="showAllFilters ? 'Hide Filters' : 'Show More Filters'"
        :icon="showAllFilters ? 'keyboard_arrow_up' : 'keyboard_arrow_down'"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { api } from 'boot/axios';
import { ref, toRaw, toRefs, watch, computed } from 'vue'; // Ensure 'computed' is imported
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
  [key: string]: string | string[] | undefined | boolean // Added string[] and boolean for filter types
}

const filters = ref<Array<Filter>>([])

const models = ref<Map>({} as Map)

for (const key in modelValue.value) {
  // Ensure correct type assignment on initialization
  models.value[key] = modelValue.value[key] as string | string[] | undefined | boolean;
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
    // Update initial state for showAllFilters based on loaded filters
    if (filters.value.length <= initialDisplayLimit || showAllFilters.value) {
      showAllFilters.value = true; // If few filters, show all by default
    } else {
      showAllFilters.value = false; // If many, hide extra by default
    }
  })
}
loadFilters()

// eslint-disable-next-line @typescript-eslint/no-unused-vars
watch(models, async () => {
  var result: Map = {} as Map
  for (const [key, value] of Object.entries(models.value)) {
    if (Array.isArray(value)) {
      if (value.length > 0) { // Only include if array has values
        result[key] = value.join(',')
      }
    } else {
      result[key] = toRaw(value);
    }
  }
  emit('update:modelValue', result);
  emit('updateFilters');
  loadFilters();
}, { deep: true });


// --- NEW REACTIVE STATE AND LOGIC FOR EXPANSION AND LAYOUT ---

// Controls if all filters are shown or just the initial limit
const showAllFilters = ref(false);

// Number of filters to show initially from the 'filters' array.
// Set to 3 to show 3 filters + the separate search input.
const initialDisplayLimit = 3;

// Computed property to determine which filters are currently visible
const visibleFilters = computed(() => {
  if (showAllFilters.value) {
    return filters.value;
  }
  return filters.value.slice(0, initialDisplayLimit);
});

// Function to toggle the expansion state
const toggleShowAllFilters = () => {
  showAllFilters.value = !showAllFilters.value;
};

// Computed property to apply responsive column classes and spreading behavior
const filterColClasses = computed(() => {
  const numVisibleFilters = visibleFilters.value.length;

  if (numVisibleFilters > 0) {
    // If there are filters visible, apply responsive spreading
    // col-xs-12: Full width on extra small screens
    // col-sm-auto: Take only necessary width on small screens, allowing multiple filters
    // col-grow: Allow items to expand and fill available space horizontally
    return 'col-xs-12 col-sm-auto col-grow';
  }
  // Fallback if no filters are visible (though unlikely if filters.length > 0)
  return '';
});

// --- END NEW REACTIVE STATE AND LOGIC ---

</script>

<style scoped>
/* Ensure minimum width for filter columns to prevent squishing text */
.col-xs-12.col-sm-auto,
.col-xs-12.col-sm-6.col-md-4.col-lg-3 {
  min-width: 150px; /* Adjust as needed for your filter content */
}
</style>