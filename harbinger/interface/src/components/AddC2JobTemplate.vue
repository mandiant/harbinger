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
  <q-card-section>
    <q-select
      v-model="template"
      :options="templates"
      label="Select a command"
    />
    <div class="q-pa-md">
      <job-template-form
        :schema="schema"
        v-model="model"
        @submit="onSubmit"
        @preview="onPreview"
        :loading="loading"
        icon="preview"
      />
    </div>
    <q-form class="q-gutter-md">
      <q-input label="command" filled readonly v-model="preview.command" />
      <q-input label="arguments" filled readonly v-model="preview.arguments" />
    </q-form>
  </q-card-section>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref, watch, toRefs } from 'vue';
import { api } from 'boot/axios';
import JobTemplateForm from '../components/JobTemplateForm.vue';
import { JobPreview } from '../models';

const $q = useQuasar();
const loading = ref(false);
const templates = ref([]);
const template = ref(null);
const schema = ref({});
const model = ref({});
const preview = ref<JobPreview>({} as JobPreview);
const tab = ref('c2');

const props = defineProps({
  modelValue: String,
  playbook_id: {
    type: String,
    default: '',
  },
});

const { playbook_id } = toRefs(props);
const emit = defineEmits(['update:modelValue']);

function onSubmit() {
  let data = model.value;
  loading.value = true;
  if (playbook_id.value !== '') {
    data.playbook_id = playbook_id;
  }
  api
    .post(`/templates/${tab.value}/${template.value}`, data)
    .then((response) => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        message: `Submitted, job_id: ${response.data.id}`,
        position: 'top',
      });
      loading.value = false;
      emit('update:modelValue', response.data.id);
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Creating failed',
        icon: 'report_problem',
      });
    });
}

watch(tab, (old, new_model) => {
  if (old !== new_model) {
    LoadTemplates();
    schema.value = {};
    model.value = {};
    template.value = null;
    preview.value = {} as JobPreview;
  }
});

function LoadTemplates() {
  api
    .get(`/templates/${tab.value}/`)
    .then((response) => {
      templates.value = response.data.templates;
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

LoadTemplates();

function onPreview() {
  api
    .post(`/templates/${tab.value}/${template.value}/preview`, model.value)
    .then((response) => {
      preview.value = response.data;
    })
    .catch(() => {
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Preview failed, are all fields filled in?',
        icon: 'report_problem',
      });
    });
}

function LoadSchema() {
  if (template.value) {
    api
      .get(`/templates/${tab.value}/${template.value}/schema`)
      .then((response) => {
        schema.value = response.data;
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
}

watch(template, (old, new_model) => {
  if (old !== new_model) {
    LoadSchema();
  }
});
</script>
