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
        <h5>Use AI to suggest actions</h5>
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <q-select v-model="type" label="Type" :options="choices" />
          <c2-implant-select v-model="form.c2_implant_id" v-if="type === 'c2_implant'" />
          <q-input filled v-model="form.prompt" autogrow type="textarea" label="additional prompt" />
          <q-toggle v-model="form.credentials" label="Credentials" :default="true" />
          <q-toggle v-model="form.playbooks" label="Playbooks" :default="true" />
          <q-toggle v-model="form.c2_tasks" label="C2 Tasks" :default="true" />
          <q-toggle v-model="form.c2_task_output" label="C2 task output" :default="true" />
          <q-toggle v-model="form.proxies" label="Proxies" :default="true" />
          <div>
            <q-btn label="Submit" type="submit" color="secondary" :loading="loading" />
            <q-btn label="Reset" type="reset" color="secondary" flat class="q-ml-sm" />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref } from 'vue';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';

import C2ImplantSelect from '../components/C2ImplantSelect.vue';


const $q = useQuasar();
const loading = ref(false);
const $router = useRouter();

const choices = ref(['c2_implant', 'domain', 'files', 'privilege_escalation']);
const type = ref('domain')

interface Form {
  prompt: string;
  c2_implant_id: string;
  credentials: boolean;
  playbooks: boolean;
  c2_tasks: boolean,
  c2_task_output: boolean,
  proxies: boolean,
}

const form = ref<Form>({
  c2_implant_id: '', credentials: true,
  playbooks: true, payloads: true,
  c2_tasks: true, c2_task_output: true,
  proxies: true, prompt: '',
} as Form);

function onSubmit() {
  api
    .post(`/suggestions/${type.value}`, form.value)
    .then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        position: 'top',
        message: 'Submitted',
      });
      $router.push({ name: 'suggestions' });
      loading.value = false;
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Creation failed',
        icon: 'report_problem',
      });
    });
}

function onReset() {
  form.value = {} as Form;
}
</script>