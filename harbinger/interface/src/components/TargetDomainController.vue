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
      v-model="domain_controller"
      option-label="name"
      :options="domain_controllers"
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
import { Node } from '../models';

const $q = useQuasar();

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  title: String,
  return_key: {
    type: String,
    default: 'name',
  },
});

const { modelValue, title, return_key } = toRefs(props);

const search = ref('');

const emit = defineEmits(['update:modelValue']);

const domain_controllers = ref([]);
const domain_controller = ref(modelValue.value);

watch(modelValue, () => {
  if (!modelValue.value) {
    domain_controller.value = null;
  }
});

function updateValue(event: Node) {
  if (event !== null) {
    emit('update:modelValue', event[return_key.value]);
  } else {
    emit('update:modelValue', null);
  }
}

function filterFn(val, update) {
  update(() => {
    search.value = val;
    loaddomaincontrollers();
  });
}

function newValue(inputValue, doneFn) {
  doneFn({ name: inputValue });
}

function loaddomaincontrollers() {
  api
    .get('/graph/domain_controllers/', { params: { search: search?.value } })
    .then((response) => {
      domain_controllers.value = response.data.items;
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
loaddomaincontrollers();
</script>
