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
    
    <div class="q-gutter-y-md">
      <q-card>
        <q-tabs
          v-model="tab"
          dense
          class="text-grey"
          active-color="primary"
          indicator-color="primary"
          align="justify"
          narrow-indicator
        >
          <q-tab
            name="mark"
            label="Mark objects as high value / owned"
            :class="$q.dark.isActive ? 'text-white' : 'text-black'"
          />
          <q-tab
            name="queries"
            label="Pre-defined queries"
            :class="$q.dark.isActive ? 'text-white' : 'text-black'"
          />
          <!-- <q-tab
            name="graph"
            label="Graph"
            :class="$q.dark.isActive ? 'text-white' : 'text-black'"
          /> -->
        </q-tabs>

        <q-separator />

        <q-tab-panels v-model="tab" animated>
          <q-tab-panel name="mark"><mark-objects /></q-tab-panel>
          <q-tab-panel name="queries"><predefined-queries /></q-tab-panel>
          <!-- <q-tab-panel name="graph"><predefined-queries-graph /></q-tab-panel> -->
        </q-tab-panels>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">

import MarkObjects from '../components/MarkObjects.vue';
import PredefinedQueries from '../components/PredefinedQueries.vue';
// import PredefinedQueriesGraph from '../components/PredefinedQueriesGraph.vue';

import { ref } from 'vue';
const tab = ref('mark');
</script>
