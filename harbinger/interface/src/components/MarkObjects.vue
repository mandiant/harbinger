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
  <q-form @submit="markObjects" @reset="resetObjects" class="q-gutter-md">
    <h5>Mark objects</h5>
    <q-input
      filled
      v-model="marked"
      label="Object names to mark"
      type="textarea"
      :rules="[(val: string) => !!val || 'Field is required']"
    />

    <q-option-group v-model="group" :options="options" color="primary" />

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
        color="secondary"
        flat
        class="q-ml-sm"
      />
    </div>
  </q-form>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';

const $q = useQuasar();

const marked = ref('');
const loading = ref(false);
const group = ref('op1');
const options = [
  {
    label: 'Owned',
    value: 'op1',
  },
  {
    label: 'High value',
    value: 'op2',
  },
  {
    label: 'Not owned',
    value: 'op3',
  },
  {
    label: 'Not high value',
    value: 'op4',
  },
];

function markObjects() {
  loading.value = true;
  let url = '';

  switch (group.value) {
    case 'op1':
      url = '/graph/mark_owned';
      break;
    case 'op2':
      url = '/graph/mark_high_value';
      break;
    case 'op3':
      url = '/graph/unmark_owned';
      break;
    case 'op4':
      url = '/graph/unmark_high_value';
      break;
    default:
      url = '/graph/mark_owned';
  }

  const names = marked.value.split('\n');

  api
    .post(url, { names: names })
    .then((response) => {
      loading.value = false;
      $q.notify({
        color: 'positive',
        position: 'top',
        message: `${response.data.count} Objects marked!`,
        icon: 'report_problem',
      });
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Unable mark objects.',
        icon: 'report_problem',
      });
    });
}

function resetObjects() {
  marked.value = '';
}
</script>
