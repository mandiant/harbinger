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
  <q-form class="q-gutter-md">
    <div>Create job from template:</div>
    <q-select
      v-model="template"
      :options="templates"
      label="Select a template"
    />
    <div class="q-pa-md">
      <job-template-form
        :schema="schema"
        v-model="model"
        @submit="onSubmit"
        @preview="onPreview"
        icon="preview"
        :loading="loading"
      />
    </div>

    <q-input
      v-if="command_line"
      v-model="command_line"
      filled
      dark
      :input-style="style"
      :bg-color="color"
    />
    <q-btn
      v-if="command_line"
      label="copy to clipboard"
      @click="clipboard"
      color="secondary"
      icon="content_copy"
    />
  </q-form>
</template>

<style>
.bg-powershell {
  background: #012456 !important;
}
.bg-bash {
  background: #2d2f38 !important;
}
</style>

<script setup lang="ts">
import { useQuasar, copyToClipboard } from 'quasar';
import { ref, watch, toRefs } from 'vue';
import { api } from 'boot/axios';
import JobTemplateForm from '../components/JobTemplateForm.vue';
import { JobPreview } from '../models';

const props = defineProps({
  modelValue: String,
  playbook_id: {
    type: String,
    default: '',
  },
});

const { playbook_id } = toRefs(props);
const emit = defineEmits(['update:modelValue']);
const $q = useQuasar();

const loading = ref(false);

function onSubmit() {
  let data = model.value;
  loading.value = true;
  if (playbook_id.value !=='') {
    data.playbook_id = playbook_id;
  }
  api
    .post(`/templates/socks/${template.value}`, data)
    .then((response) => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        position: 'top',
        message: `Submitted, job_id: ${response.data.id}`,
      });
      emit('update:modelValue', response.data.id);
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

const templates = ref([]);
const template = ref(null);
const schema = ref({});
const model = ref({});

function LoadTemplates() {
  api
    .get('/templates/socks/')
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

const preview = ref<JobPreview>({} as JobPreview);
const command_line = ref('');
const style = ref('');
const color = ref('');

function onPreview() {
  api
    .post(`/templates/socks/${template.value}/preview`, model.value)
    .then((response) => {
      preview.value = response.data;
      if (response.data.socks_server && response.data.socks_server.operating_system == 'linux') {
        command_line.value = `[user:~]$ ${preview.value.command} ${preview.value.arguments}\n`;
        style.value = "font-family: 'Fira Code', monospace;";
        color.value = 'bash';
      } else {
        command_line.value = `PS C:\\ > ${preview.value.command} ${preview.value.arguments}\n`;
        style.value = "font-family: 'Consolas';";
        color.value = 'powershell';
      }
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        position: 'top',
        message: 'Preview loaded!',
      });
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

function clipboard() {
  copyToClipboard(`${preview.value.command} ${preview.value.arguments}`)
    .then(() => {
      // success!
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        message: 'Command copied to clipboard!',
        position: 'top',
      });
    })
    .catch(() => {
      // fail
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Failed to copy to clipboard',
        icon: 'report_problem',
      });
    });
}

function LoadSchema() {
  api
    .get(`/templates/socks/${template.value}/schema`)
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

watch(template, (old, new_model) => {
  if (old !== new_model) {
    LoadSchema();
  }
});
</script>
