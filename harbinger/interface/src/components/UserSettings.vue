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
  <div>
    <q-form @submit="onSubmit" class="q-gutter-md">
      <q-input v-model="me.email" label="Email" />
      <q-input v-model="me.password" filled :type="isPwd ? 'password' : 'text'" label="New password">
        <template v-slot:append>
          <q-icon
            :name="isPwd ? 'visibility_off' : 'visibility'"
            class="cursor-pointer"
            @click="isPwd = !isPwd"
          />
        </template>
      </q-input>
      <q-btn
        label="Submit"
        type="submit"
        color="secondary"
        :loading="loading"
      />
    </q-form>
  </div>
</template>

<script setup lang="ts">
import { api } from 'boot/axios';
import { ref } from 'vue';
import { HarbingerUser } from 'src/models';
import { useQuasar } from 'quasar';

const $q = useQuasar();

const me = ref<HarbingerUser>({} as HarbingerUser);
const isPwd = ref(true);
const loading = ref(false);

function LoadData() {
  loading.value = true;
  api.get('/users/me').then((response) => {
    me.value = response.data;
    loading.value = false;
  })
}
LoadData();

function onSubmit() {
  loading.value = true;
  api.patch('/users/me', me.value).then(() => {
    loading.value = false;
    LoadData();
  }).catch(() => {
    loading.value = false;
        $q.notify({
          color: 'negative',
          position: 'top',
          message: 'Saving failed',
          icon: 'report_problem',
        });
  })
}

</script>
