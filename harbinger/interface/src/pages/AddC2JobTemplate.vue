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
    <bread-crumb />
    <q-card flat class="q-pa-md">
      <add-c2-job-template v-model="job_id" @update:model-value="Goto()" />
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import BreadCrumb from '../components/BreadCrumb.vue';
import AddC2JobTemplate from 'src/components/AddC2JobTemplate.vue';
import { useRouter } from 'vue-router';

const $router = useRouter();
const job_id = ref('');

function Goto() {
  $router.push({ name: 'c2_job', params: { id: job_id.value } });
}
</script>
