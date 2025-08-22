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
        <h5>Add a credential</h5>
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <q-input filled v-model="username" label="username" :error="!username"  lazy-rules/>
          <q-select v-model="password" :option-label="(opt) => formatPassword(opt)" :options="passwords" label="Password"
            @filter="filterFn" clearable filled use-input :error="!password.id" lazy-rules />
          <domain-select v-model:model-value="domain_id"/>
          <q-toggle v-model="markowned" label="Mark credential owned in neo4j?"></q-toggle>
          <div>
            <q-btn label="Submit" type="submit" color="secondary" :loading="loading" />
            <q-btn label="Reset" type="reset" color="seconday" flat class="q-ml-sm" />
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

import { Password } from '../models';
import DomainSelect from 'src/components/DomainSelect.vue';

const $router = useRouter();
const passwords = ref<Array<Password>>([]);
const domain_id = ref('');
const password = ref({} as Password);
const username = ref('');
const search = ref('');
const loading = ref(false);
const markowned = ref(true);

function formatPassword(obj: Password) {
  if (obj === null) {
    return 'null';
  }
  if (obj.password !== null) {
    return obj.password;
  }
  if (obj.nt !== null) {
    return obj.nt;
  }
  if (obj.aes128_key !== null) {
    return obj.aes128_key;
  }
  if (obj.aes256_key !== null) {
    return obj.aes256_key;
  }
}

function loadPasswords() {
  api
    .get('/passwords/', { params: { search: search?.value } })
    .then((response) => {
      passwords.value = response.data.items;
    })
    .catch(() => {
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Loading failed',
        icon: 'report_problem',
      });
    });
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars
function filterFn(val: any, update: any, abort: any) {
  update(() => {
    search.value = val;
    loadPasswords();
  });
}

loadPasswords();

const $q = useQuasar();

function onSubmit() {
  if (
    password.value != null &&
    username.value != null
  ) {
    loading.value = true;
    api
      .post('/credentials/', {
        password_id: password.value.id,
        domain_id: domain_id.value,
        username: username.value,
        mark_owned: markowned.value,
      })
      .then((response) => {
        $q.notify({
          color: 'green-4',
          textColor: 'white',
          icon: 'cloud_done',
          position: 'top',
          message: `Submitted, id: ${response.data.id}`,
        });
        $router.push({ name: 'credentials' });
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
  password.value = {} as Password;
  domain_id.value = '';
  username.value = '';
}
</script>
