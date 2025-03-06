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
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <h5>Create a timeline document</h5>

          <div class="row q-gutter-md">
            <q-input v-model="hour_offset" type="number" label="Hour offset" />

            <q-toggle v-model="create_screenshot" label="Create screenshots?" />

            <q-select v-model="theme" :options="theme_options" label="Theme for the screenshots" />
          </div>

          <q-btn label="Submit" type="submit" color="secondary" :loading="loading" />
          <q-btn label="Reset" type="reset" color="secondary" flat class="q-ml-sm" />
        </q-form>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref } from 'vue';
import { api } from 'boot/axios'
import { useRouter } from 'vue-router';

import BreadCrumb from '../components/BreadCrumb.vue';

const hour_offset = ref(0);
const loading = ref(false);
const theme = ref('asciinema');
const create_screenshot = ref(true);
const $q = useQuasar();
const $router = useRouter();

const theme_options = ['asciinema', 'dracula', 'github_dark', 'github-light', 'monokai', 'nord', 'solarized-dark', 'solarized-light']

function onSubmit() {
  api.post('/create_timeline/', { theme: theme.value, create_screenshots: create_screenshot.value, hour_offset: hour_offset.value }).then(() => {
    $q.notify({
      color: 'green-4',
      textColor: 'white',
      icon: 'cloud_done',
      position: 'top',
      message: 'Timeline creation scheduled, a new file will appear when its done.',
    });
    loading.value = false;
    $router.push({ name: 'timeline' });
  }).catch(() => {
    loading.value = false;
    $q.notify({
      color: 'negative',
      position: 'top',
      message: 'Error creating timeline.',
      icon: 'report_problem',
    });
  });
}

function onReset() {
  theme.value = 'asciinema'
  create_screenshot.value = true
  hour_offset.value = 0
}

</script>
