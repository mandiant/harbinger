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
  <div class="window-height window-width row wrap justify-center items-center">
    <q-card flat class="col-8">
      <q-card-section>
        <q-form class="q-gutter-md" @submit="onSubmit" @reset="onReset">
          <h5>Login</h5>
          <q-input filled v-model="username" label="Username" lazy-rules />
          <q-input filled v-model="password" label="Password" type="password" />
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
        </q-form>
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref } from 'vue';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';

const $q = useQuasar();
const $router = useRouter();

const username = ref(null);
const password = ref(null);
const loading = ref(false);

function onSubmit() {
  if (username.value != null && password.value != null) {
    loading.value = true;
    api
      .post(
        '/auth/login',
        new URLSearchParams({
          username: username.value,
          password: password.value,
        }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      )
      .then(() => {
        $q.notify({
          color: 'green-4',
          position: 'top',
          textColor: 'white',
          icon: 'cloud_done',
          message: 'Logged in!',
        });
        loading.value = false;
        $router.push('/');
      })
      .catch(() => {
        loading.value = false;
        $q.notify({
          color: 'negative',
          position: 'top',
          message: 'Username or password is incorrect',
          icon: 'report_problem',
        });
      });
  } else {
    $q.notify({
      color: 'red-5',
      textColor: 'white',
      icon: 'warning',
      message: 'You need to fill in everything',
      position: 'top',
    });
  }
}

function onReset() {
  username.value = null;
  password.value = null;
}
</script>
