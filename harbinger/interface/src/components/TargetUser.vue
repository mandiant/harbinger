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
    <q-select
      v-model="user"
      option-label="name"
      :options="users"
      :label="title"
      clearable
      @update:model-value="updateValue"
      @filter="filterFn"
      @new-value="newValue"
      filled
      use-input
    />
  </div>
</template>

<script setup lang="ts">
import { ref, toRefs, watch } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';

const $q = useQuasar();

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  title: String,
});

const { modelValue, title } = toRefs(props);

const search = ref('');

const emit = defineEmits(['update:modelValue']);

const users = ref([]);
const user = ref(modelValue.value);

watch(modelValue, () => {
  if (!modelValue.value) {
    user.value = null;
  } else {
    user.value = modelValue.value;
  }
});

function updateValue(event) {
  if (event !== null) {
    emit('update:modelValue', event.name);
  } else {
    emit('update:modelValue', null);
  }
}

function filterFn(val, update) {
  update(() => {
    search.value = val;
    loadusers();
  });
}

function newValue(inputValue, doneFn) {
  doneFn({ name: inputValue });
}

function loadusers() {
  api
    .get('/graph/users/', { params: { search: search?.value } })
    .then((response) => {
      users.value = response.data.items;
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
loadusers();
</script>
