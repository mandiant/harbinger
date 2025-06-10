<template>
  <q-page padding>
    <bread-crumb />
    <q-card flat class="q-pa-md">
      <q-stepper
        v-model="step"
        ref="stepperRef"
        color="primary"
        animated
        flat
      >
        <q-step
          :name="1"
          title="Input README"
          icon="description"
          :done="step > 1"
          :header-nav="step > 1"
        >
          <q-form @submit="onSubmitReadme" @reset="onResetReadme" class="q-gutter-md">
            <q-input
              v-model="readmeContent"
              filled
              type="textarea"
              label="Paste README content here"
              hint="Provide the README markdown content to generate a playbook template."
              autogrow
              class="q-mb-md"
              :readonly="loadingReadme"
            />
            <q-btn
              label="Generate Template"
              type="submit"
              color="secondary"
              :loading="loadingReadme"
            />
            <q-btn
              label="Clear"
              type="reset"
              color="secondary"
              flat
              class="q-ml-sm"
              :disable="loadingReadme"
            />
          </q-form>
        </q-step>

        <q-step
          :name="2"
          title="Review & Submit Template"
          icon="code"
          :header-nav="step > 0"
        >
           <q-btn
              label="« Start Over with new README"
              icon="arrow_back"
              color="grey"
              flat
              size="sm"
              class="q-mb-sm"
              @click="resetAll"
              :disable="loadingYaml"
           />
          <q-form @submit="onSubmitYaml" class="q-gutter-md">
            <monaco-editor
              v-model="generatedYaml"
              :readonly="loadingYaml"
              language="yaml"
              style="min-height: 400px; border: 1px solid #ddd"
              class="q-mb-md"
            />
            <q-btn
              label="Submit Template"
              type="submit"
              color="secondary"
              :loading="loadingYaml"
            />
          </q-form>
        </q-step>
      </q-stepper>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref } from 'vue';
import { api } from 'boot/axios';
import BreadCrumb from '../components/BreadCrumb.vue';
import { useRouter } from 'vue-router';
import { useParamStore } from 'src/stores/ParamStore';
import MonacoEditor from '../components/MonacoEditor.vue';

const $q = useQuasar();
const $router = useRouter();
const p_store = useParamStore();

// --- State Refs ---
const step = ref(1);
const stepperRef = ref(null);
const readmeContent = ref('');
const generatedYaml = ref('');
const loadingReadme = ref(false);
const loadingYaml = ref(false);

// --- Functions ---
function onSubmitReadme() {
  if (readmeContent.value.trim() === '') {
    $q.notify({ color: 'red-5', message: 'Please paste README content...', position: 'top' });
    return;
  }
  loadingReadme.value = true;
  api.post('/templates/playbooks/ai', { readme: readmeContent.value })
    .then((response) => {
      if (response.data && typeof response.data.yaml === 'string') {
          generatedYaml.value = response.data.yaml;
          step.value = 2;
          $q.notify({ color: 'green-4', message: 'Template generated...', position: 'top',});
      } else { throw new Error('Invalid response format'); }
    })
    .catch((error) => { 
      if(error.response.data) {
        $q.notify({ color: 'negative', message: `Generation failed: ${error.response.data}`, position: 'top',});
      } else {
        $q.notify({ color: 'negative', message: `Generation failed: ${error.message}`, position: 'top',});
      }
    })
    .finally(() => { loadingReadme.value = false; });
}

function onResetReadme() { readmeContent.value = ''; }

function onSubmitYaml() {
  if (generatedYaml.value.trim() === '') {
     $q.notify({ color: 'red-5', message: 'Generated YAML content cannot be empty.', position: 'top',});
    return;
  }
  loadingYaml.value = true;
  api.post('/templates/playbooks/', { yaml: generatedYaml.value })
    .then((response) => {
      $q.notify({ color: 'green-4', message: `Submitted successfully, id: ${response.data.id}` });
      p_store.setPlaybookTemplate(response.data.id);
      $router.push({ name: 'add_playbook_from_template' });
    })
    .catch((error) => {
      loadingYaml.value = false;
      $q.notify({ color: 'negative', message: `Submission failed: ${error.message}` });
    })
    .finally(() => { loadingYaml.value = false; });
}

function resetAll() {
    readmeContent.value = '';
    generatedYaml.value = '';
    loadingReadme.value = false;
    loadingYaml.value = false;
    step.value = 1;
}
</script>

<style scoped>
/* Keep existing styles */
.q-mb-md { margin-bottom: 16px; }
.q-mb-sm { margin-bottom: 8px; }
.monaco-editor {
  min-height: 400px;
  border: 1px solid #ddd;
}
</style>