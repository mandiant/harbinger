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
  <q-item>
    <q-item-section>
      <q-item-label>{{ suggestion.name }}</q-item-label>
      <q-item-label caption>{{ suggestion.reason }}</q-item-label>
    </q-item-section>
    <q-item-section side>
      <div class="row q-gutter-sm">
        <q-btn
          flat
          dense
          round
          color="primary"
          icon="info"
          @click="showDetails = true"
        >
          <q-tooltip>Details</q-tooltip>
        </q-btn>
        <q-btn
          flat
          dense
          color="secondary"
          icon="add_circle"
          label="Create playbook"
          :to="{ name: 'suggestion_create', params: { id: suggestion.id } }"
        />
      </div>
    </q-item-section>

    <q-dialog v-model="showDetails">
      <q-card style="width: 600px; max-width: 80vw;">
        <q-card-section>
          <div class="text-h6">Suggestion Details</div>
        </q-card-section>

        <q-card-section class="q-pt-none" :class="[$q.dark.isActive ? 'bg-grey-9' : 'bg-grey-2']">
          <pre>{{ JSON.stringify(suggestion, null, 2) }}</pre>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Close" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-item>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import { Suggestion } from 'src/models';

defineProps({
  suggestion: {
    type: Object as () => Suggestion,
    required: true,
  },
});

const $q = useQuasar();
const showDetails = ref(false);
</script>

<style scoped>
pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
