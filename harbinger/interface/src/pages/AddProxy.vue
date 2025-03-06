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
      <q-card-section>
        <h5>Add a proxy</h5>
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <q-input
            filled
            v-model="host"
            label="host"
            :rules="[(val) => !!val || 'Field is required']"
          />
          <q-input
            filled
            v-model="port"
            label="port"
            type="number"
            :rules="[
              (val) =>
                (!!val && val > 0 && val < 65536) ||
                'Port must be between 1 and 65535',
            ]"
          />
          <q-input
            filled
            v-model="type"
            label="type"
            :rules="[(val) => !!val || 'Field is required']"
          />
          <q-input filled v-model="status" label="status" />
          <q-input filled v-model="remote_hostname" label="remote hostname" />
          <q-input filled v-model="username" label="proxy username" />
          <q-input filled v-model="password" label="proxy password" />

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
import BreadCrumb from '../components/BreadCrumb.vue';
const $q = useQuasar();
const $router = useRouter();

const loading = ref(false);

const host = ref('localhost');
const port = ref(0);
const type = ref('socks4');
const status = ref('connected');
const remote_hostname = ref('');

const username = ref('');
const password = ref('');

function onSubmit() {
  loading.value = true;
  api
    .post('/proxies/', {
      host: host.value,
      port: port.value,
      type: type.value,
      status: status.value,
      remote_hostname: remote_hostname.value,
      username: username.value,
      password: password.value,
    })
    .then((response) => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        position: 'top',
        message: `Submitted, job_id: ${response.data.id}`,
      });
      $router.push({ name: 'proxies' });
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
}

function onReset() {
  host.value = 'localhost';
  port.value = 0;
  type.value = 'socks4';
  status.value = 'connected';
  remote_hostname.value = '';
  username.value = '';
  password.value = '';
}
</script>
