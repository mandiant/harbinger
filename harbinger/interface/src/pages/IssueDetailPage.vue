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
    <q-card v-if="issue">
      <q-card-section>
        <div class="text-h6">Issue Details</div>
      </q-card-section>

      <q-separator />

      <q-card-section>
        <q-list bordered>
          <q-item>
            <q-item-section>
              <q-item-label overline>Name</q-item-label>
              <q-item-label>{{ issue.name }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label overline>Description</q-item-label>
              <q-item-label style="white-space: pre-wrap;">{{ issue.description }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label overline>Impact</q-item-label>
              <q-item-label>{{ issue.impact }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label overline>Exploitability</q-item-label>
              <q-item-label>{{ issue.exploitability }}</q-item-label>
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
import { Issue } from 'src/models';

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
});

const issue = ref<Issue | null>(null);

const fetchIssue = async () => {
  try {
    issue.value = null;
    const response = await api.get<Issue>(`/issues/${props.id}`);
    issue.value = response.data;
  } catch (error) {
    console.error('Error fetching issue:', error);
  }
};

watch(() => props.id, fetchIssue);

onMounted(fetchIssue);
</script>
