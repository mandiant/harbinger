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
    
    <q-card flat class="q-pa-md">
      <q-card-section>
        <add-proxy-job-template v-model="job_id" @update:model-value="Goto()" />
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import AddProxyJobTemplate from 'src/components/AddProxyJobTemplate.vue';
import { useRouter } from 'vue-router';

const $router = useRouter();
const job_id = ref(0);

function Goto() {
  $router.push({ name: 'proxy_job', params: { id: job_id.value } });
}
</script>
