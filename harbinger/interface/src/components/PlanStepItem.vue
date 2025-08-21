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
  <q-expansion-item
    v-model="isExpanded"
    expand-separator
    :label="planStep.description"
    :caption="`Step ${planStep.order}`"
    header-class="text-body1"
  >
    <template v-slot:header>
      <q-item-section avatar>
        <q-avatar :color="statusColor" text-color="white">
          {{ planStep.order }}
        </q-avatar>
      </q-item-section>

      <q-item-section>
        <q-item-label class="text-body1">{{ planStep.description }}</q-item-label>
        <q-item-label caption>{{ planStep.status }}</q-item-label>
      </q-item-section>

      <q-item-section side>
        <llm-status-indicator :status="planStep.llm_status" />
      </q-item-section>
    </template>

    <q-card>
      <q-card-section>
        <div class="text-subtitle2">Notes</div>
        <p class="text-body2 q-mt-sm" style="white-space: pre-wrap;">{{ planStep.notes }}</p>
      </q-card-section>

      <q-card-section v-if="planStep.suggestions && planStep.suggestions.length > 0" class="q-pt-none">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle2">Suggestions</div>
          </q-card-section>
          <q-separator />
          <q-list separator>
            <suggestion-item
              v-for="suggestion in planStep.suggestions"
              :key="suggestion.id"
              :suggestion="suggestion"
            />
          </q-list>
        </q-card>
      </q-card-section>
    </q-card>
  </q-expansion-item>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { PlanStep } from 'src/models';
import LlmStatusIndicator from './LlmStatusIndicator.vue';
import SuggestionItem from './SuggestionItem.vue';

const props = defineProps({
  planStep: {
    type: Object as () => PlanStep,
    required: true,
  },
});

const isExpanded = defineModel<boolean>('expanded');

const statusColor = computed(() => {
  switch (props.planStep.status) {
    case 'SUCCESS':
      return 'positive';
    case 'ERROR':
      return 'negative';
    case 'PENDING':
      return 'grey';
    default:
      return 'primary';
  }
});
</script>