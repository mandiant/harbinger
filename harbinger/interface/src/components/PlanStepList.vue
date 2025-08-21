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
  <q-list separator>
    <plan-step-item
      v-for="step in data"
      :key="step.id"
      :plan-step="step"
      v-model:expanded="expansionState[step.id]"
    />
  </q-list>
</template>

<script setup lang="ts">
import { ref, toRefs, watch, computed } from 'vue';
import { PlanStep } from 'src/models';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia';
import PlanStepItem from './PlanStepItem.vue';

const props = defineProps({
  planId: {
    type: String,
    required: false,
  },
});

const { planId } = toRefs(props);

const useStore = defineTypedStore<PlanStep>('plan_steps');
const store = useStore();
const { data } = storeToRefs(store);

// Watch for changes in planId to correctly reload data
watch(planId, (newPlanId) => {
  // 1. Immediately clear existing data to prevent showing stale steps
  store.data = [];
  // 2. Reset filters to ensure we don't mix old and new plan_id filters
  store.filters = {};

  // 3. If a new planId is provided, apply the filter and load the data
  if (newPlanId) {
    store.AddFilter({ plan_id: newPlanId });
    store.LoadData();
  }
}, { immediate: true }); // immediate: true ensures this runs on component mount

const expansionState = ref<Record<string, boolean>>({});

const allExpanded = computed(() => {
  if (data.value.length === 0) return false;
  return data.value.every(step => expansionState.value[step.id]);
});

function toggleAll() {
  const expand = !allExpanded.value;
  data.value.forEach(step => {
    expansionState.value[step.id] = expand;
  });
}

function refresh() {
  store.LoadData();
}

defineExpose({
  toggleAll,
  refresh,
  allExpanded,
});
</script>
