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
        <h5>Add a domain</h5>
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <q-input filled v-model="short_name" label="Shortname" lazy-rules />

          <q-input filled v-model="long_name" label="longname" />

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

const short_name = ref(null);
const long_name = ref(null);
const loading = ref(false);

function onSubmit() {
  if (short_name.value != null) {
    loading.value = true;
    api
      .post('/domains/', {
        short_name: short_name.value,
        long_name: long_name.value,
      })
      .then((response) => {
        $q.notify({
          color: 'green-4',
          textColor: 'white',
          icon: 'cloud_done',
          position: 'top',
          message: `Submitted, domain_id: ${response.data.id}`,
        });
        $router.push({ name: 'domains' });
        loading.value = false;
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
  short_name.value = null;
  long_name.value = null;
}
</script>
