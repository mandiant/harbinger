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
        <h5>Add a playbook template</h5>
        <monaco-editor v-model="yaml" :readonly="false" language="yaml" />
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <div>
            <q-btn
              label="Submit"
              type="submit"
              color="secondary"
              :loading="loading"
            />
            <q-btn
              label="Reset"
              type="reset"
              color="seconday"
              flat
              class="q-ml-sm"
            />
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

import { v4 as uuidv4 } from 'uuid';
import { useRouter } from 'vue-router';
import { useParamStore } from 'src/stores/ParamStore';
import MonacoEditor from '../components/MonacoEditor.vue';

const $q = useQuasar();
const $router = useRouter();

const p_store = useParamStore();

const yaml = ref(`id: ${uuidv4()}
icon: plus
name: New playbook
step_delay: 0

args:
- name: argument1
  type: str
  default: argument1

steps: |
  - type: c2
    name: sleep
    args:
      - name: sleep
        value: 0
`);
const loading = ref(false);

function onSubmit() {
  if (yaml.value !== '') {
    loading.value = true;
    api
      .post('/templates/playbooks/', {
        yaml: yaml.value,
      })
      .then((response) => {
        $q.notify({
          color: 'green-4',
          textColor: 'white',
          icon: 'cloud_done',
          position: 'top',
          message: `Submitted, template_playbook_id: ${response.data.id}`,
        });
        loading.value = false;
        p_store.setPlaybookTemplate(response.data.id)
        $router.push({ name: 'add_playbook_from_template' });
      })
      .catch((error) => {
        loading.value = false;
        $q.notify({
          color: 'negative',
          position: 'top',
          message: `Creation failed: ${error.response.data}`,
          icon: 'report_problem',
        });
      });
  } else {
    $q.notify({
      color: 'red-5',
      textColor: 'white',
      icon: 'warning',
      position: 'top',
      message: 'You need to fill in everything',
    });
  }
}

function onReset() {
  yaml.value = `id: ${uuidv4()}
icon: add
name: New playbook
step_delay: 0

args:
- name: argument1
  type: str
  default: argument1

steps: |
  - type: c2
    name: sleep
    args:
      - name: sleep
        value: 0
`
;
}
</script>
