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
  <q-page class="q-pa-md">
    <q-card v-if="c2Output">
      <q-card-section>
        <div class="text-h6">C2 Output Details</div>
      </q-card-section>

      <q-separator />

      <q-card-section>
        <q-list bordered>
          <q-item>
            <q-item-section>
              <q-item-label overline>ID</q-item-label>
              <q-item-label>{{ c2Output.id }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label overline>Timestamp</q-item-label>
              <q-item-label>{{ new Date(c2Output.timestamp).toLocaleString() }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label overline>Output Type</q-item-label>
              <q-item-label>{{ c2Output.output_type }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label overline>Response Text</q-item-label>
              <q-item-label style="white-space: pre-wrap; font-family: monospace;">{{ c2Output.response_text }}</q-item-label>
            </q-item-section>
          </q-item>

        </q-list>
      </q-card-section>
    </q-card>
    <div v-else class="text-center q-pa-md">
      <q-spinner-dots color="primary" size="40px" />
      <p>Loading...</p>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { api } from 'boot/axios';
import { C2Output } from 'src/models';

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
});

const c2Output = ref<C2Output | null>(null);

const fetchC2Output = async () => {
  try {
    // Set to null to show loading spinner on re-navigation
    c2Output.value = null; 
    const response = await api.get<C2Output>(`/c2_output/${props.id}`);
    c2Output.value = response.data;
  } catch (error) {
    console.error('Error fetching C2 output:', error);
    // Optionally, handle the error in the UI
  }
};

// Watch for changes in the id prop and refetch data
watch(() => props.id, () => {
  fetchC2Output();
});

onMounted(() => {
  fetchC2Output();
});
</script>
