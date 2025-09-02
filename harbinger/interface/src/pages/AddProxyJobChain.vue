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
        <h5>Add a playbook</h5>
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <q-input filled v-model="playbook_name" label="Name" lazy-rules />

          <q-input filled v-model="description" label="Description" />

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
import { useRouter } from 'vue-router';


const $q = useQuasar();
const $router = useRouter();

const playbook_name = ref('');
const description = ref('');
const loading = ref(false);

function onSubmit() {
  loading.value = true;
  api
    .post('/playbooks/', {
      playbook_name: playbook_name.value,
      description: description.value,
    })
    .then((response) => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        message: 'Submitted',
        position: 'top',
      });
      $router.push({ name: 'playbook', params: { id: response.data.id } });
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Loading failed',
        icon: 'report_problem',
      });
    });
}

function onReset() {
  playbook_name.value = '';
  description.value = '';
}
</script>
