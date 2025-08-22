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
        <h5>Add a password</h5>
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <q-input filled v-model="password" label="Password" lazy-rules />
          <q-input
            filled
            v-model="nt"
            label="nt"
            :rules="[
              (val) =>
                val === null ||
                val.length === 32 ||
                'Please use exactly 32 characters',
            ]"
          />
          <q-input filled v-model="aes128_key" label="aes128" />
          <q-input filled v-model="aes256_key" label="aes256" />

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

const password = ref(null);
const nt = ref(null);
const aes256_key = ref(null);
const aes128_key = ref(null);
const loading = ref(false);

function onSubmit() {
  if (
    password.value != null ||
    nt.value != null ||
    aes128_key.value != null ||
    aes256_key.value != null
  ) {
    loading.value = true;
    api
      .post('/passwords/', {
        password: password.value,
        nt: nt.value,
        aes256_key: aes256_key.value,
        aes128_key: aes128_key.value,
      })
      .then((response) => {
        $q.notify({
          color: 'green-4',
          textColor: 'white',
          icon: 'cloud_done',
          position: 'top',
          message: `Submitted, id: ${response.data.id}`,
        });
        $router.push({ name: 'passwords' });
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
      message: 'You need to fill in one of the 4 values',
    });
  }
}

function onReset() {
  password.value = null;
  nt.value = null;
  aes128_key.value = null;
  aes256_key.value = null;
}
</script>
