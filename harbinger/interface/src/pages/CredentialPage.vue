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
    <q-card v-if="credential">
      <q-card-section>
        <div class="text-h6">Credential Details</div>
      </q-card-section>

      <q-separator />

      <q-card-section>
        <q-list bordered>
          <q-item>
            <q-item-section>
              <q-item-label overline>ID</q-item-label>
              <q-item-label>{{ credential.id }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item>
            <q-item-section>
              <q-item-label overline>Username</q-item-label>
              <q-item-label>{{ credential.username }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item v-if="credential.domain">
            <q-item-section>
              <q-item-label overline>Domain</q-item-label>
              <q-item-label>{{ credential.domain.long_name }} ({{ credential.domain.short_name }})</q-item-label>
            </q-item-section>
          </q-item>

          <q-item v-if="credential.password">
            <q-item-section>
              <q-item-label overline>Password</q-item-label>
              <q-item-label style="font-family: monospace;">{{ credential.password.password }}</q-item-label>
            </q-item-section>
          </q-item>
          
          <q-item v-if="credential.kerberos">
            <q-item-section>
              <q-item-label overline>Kerberos Ticket</q-item-label>
              <q-item-label>Hash: {{ credential.kerberos.hash }}</q-item-label>
            </q-item-section>
          </q-item>

          <q-item v-if="credential.note">
            <q-item-section>
              <q-item-label overline>Note</q-item-label>
              <q-item-label style="white-space: pre-wrap;">{{ credential.note }}</q-item-label>
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
import { Credential } from 'src/models';

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
});

const credential = ref<Credential | null>(null);

const fetchCredential = async () => {
  try {
    credential.value = null;
    const response = await api.get<Credential>(`/credentials/${props.id}`);
    credential.value = response.data;
  } catch (error) {
    console.error('Error fetching credential:', error);
  }
};

watch(() => props.id, fetchCredential);

onMounted(fetchCredential);
</script>
