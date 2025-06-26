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
      <q-card-section v-if="playbook_template">
        <q-card-section>
          <q-item>
            <q-item-section avatar>
              <q-icon :name="playbook_template.icon" size="4em" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ playbook_template.name }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-card-section>
        <q-item v-if="preview_errors">
          <q-item-section avatar>
            <q-avatar>
              <q-icon name="error" color="secondary" />
            </q-avatar>
          </q-item-section>
          <q-item-section v-if="preview_errors">
            <q-item-label caption>
              {{ preview_errors }}
            </q-item-label>
          </q-item-section>
        </q-item>

        <q-item v-for="error in errors" v-bind:key="error">
          <q-item-section avatar>
            <q-avatar>
              <q-icon name="error" color="secondary" />
            </q-avatar>
          </q-item-section>

          <q-item-section>
            <q-item-label>{{ error.loc.join(', ') }}</q-item-label>
            <q-item-label caption>
              {{ error.msg }}
            </q-item-label>
          </q-item-section>
        </q-item>
        <job-template-form :schema="schema" v-model="model" :show_preview_button="true" :loading="loading"
          @submit="onSubmit" @preview="onPreview" />

        <q-card-section v-if="preview">
          <q-input label="Preview" type="textarea" autogrow readonly v-model="preview" :error="!preview_valid"
            error-message="Steps are not valid." />
        </q-card-section>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { toRefs, ref } from 'vue';
import { useRouter } from 'vue-router';
import BreadCrumb from 'src/components/BreadCrumb.vue';
import { Suggestion } from 'src/models';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import JobTemplateForm from '../components/JobTemplateForm.vue';
import { Schema, PlaybookTemplate } from '../models'

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
});

const { id } = toRefs(props);


const $q = useQuasar();
const $router = useRouter();
const loading = ref(false);
const object = ref<Suggestion>({} as Suggestion);

const schema = ref({} as Schema);
const model = ref({});

function LoadSchema() {
  api
    .get(`/templates/playbooks/${object.value.playbook_template_id}/schema`, { params: { suggestion_id: id.value } })
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

const playbook_template = ref({} as PlaybookTemplate)

function LoadPlaybookTemplate() {
  api
    .get(`/templates/playbooks/${object.value.playbook_template_id}`)
    .then((response) => {
      playbook_template.value = response.data;
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


function loadSuggestion() {
  loading.value = true;
  api
    .get(`/suggestions/${id.value}`)
    .then((response) => {
      object.value = response.data;
      loading.value = false;
      LoadSchema();
      LoadPlaybookTemplate();
    })
    .catch((error) => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: `Loading failed: ${error.message}`,
        icon: 'report_problem',
      });
    });
}

function onSubmit() {
  loading.value = true;
  api
    .post(`templates/playbooks/${object.value.playbook_template_id}`, model.value)
    .then((response) => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        message: 'Submitted ',
        position: 'top',
      });
      $router.push({ name: 'playbook', params: { id: response.data.id } });
    })
    .catch((error) => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Loading failed',
        icon: 'report_problem',
      });
      errors.value = error.response.data
    });
}

const errors = ref([]);
const preview = ref('');
const preview_valid = ref(true);
const preview_errors = ref('');

function onPreview() {
  loading.value = true;
  api
    .post(`templates/playbooks/${object.value.playbook_template_id}/preview`, model.value)
    .then((response) => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        message: 'Preview loaded, ',
        position: 'top',
      });
      preview.value = response.data.steps;
      preview_valid.value = response.data.valid;
      preview_errors.value = response.data.errors;
      errors.value = []
      if (response.data.steps_errors) {
        errors.value = JSON.parse(response.data.steps_errors);
      }
    })
    .catch((error) => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'preview failed',
        icon: 'report_problem',
      });
      errors.value = error.response.data;
      preview_errors.value = '';
    });
}

loadSuggestion()
</script>