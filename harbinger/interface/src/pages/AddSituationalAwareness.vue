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
        <h5>Add a situational awareness entry</h5>
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <q-input filled v-model="data.name" label="name" lazy-rules :error="!data.name" />
          <q-input filled v-model="data.category" label="category" lazy-rules :error="!data.name" />
          <q-input filled v-model="data.value_string" label="string value" />
          <q-input type="number" filled v-model="data.value_int" label="number value" />
          <q-toggle filled v-model:model-value="data.value_bool" label="boolean value" />
          <domain-select v-model:model-value="data.domain_id" :optional="true"/>
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

import DomainSelect from 'src/components/DomainSelect.vue';


const $q = useQuasar();
const $router = useRouter();

const loading = ref(false);

interface Form {
  name: string;
  category: string;
  value_string?: string | null;
  value_bool?: boolean | null;
  value_int?: number | null;
  domain_id?: string | null;
}

const data = ref({} as Form)

function onSubmit() {
  if (data.value.name != null && data.value.category != null) {
    loading.value = true;
    api
      .post('/situational_awareness/', data.value)
      .then(() => {
        $q.notify({
          color: 'green-4',
          textColor: 'white',
          icon: 'cloud_done',
          position: 'top',
          message: 'Created',
        });
        $router.push({ name: 'situational_awareness' });
        loading.value = false;
      })
      .catch((error) => {
        loading.value = false;
        $q.notify({
          color: 'negative',
          position: 'top',
          message: `Loading failed: ${JSON.stringify(error.response.data.detail)}`,
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
  data.value = {} as Form
}

</script>
