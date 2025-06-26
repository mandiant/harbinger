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
        <q-splitter v-model="splitterModel">
          <template v-slot:before>
            <q-tabs v-model="tab" vertical>
              <q-tab v-for="template in data" :icon="template.icon" v-bind:key="template.id" :name="template.id"
                :label="template.name" />
            </q-tabs>
            <div class="column items-center">
              <q-pagination v-model="current" direction-links :max="pages" flat color="grey" active-color="primary" />
            </div>
          </template>
          <template v-slot:after>
            <filter-view object-type="templates/playbooks" v-model="filters" v-on:updateFilters="updateFilters" />
            <q-tab-panels v-model="tab" animated swipeable vertical transition-prev="jump-up" transition-next="jump-up">
              <q-tab-panel :name="template.id" v-for="template in data" v-bind:key="template.id">
                <q-card flat>
                  <q-card-section>
                    <q-item>
                      <q-item-section avatar>
                        <q-icon :name="template.icon" size="4em" />
                      </q-item-section>
                      <q-item-section>
                        <q-item-label>{{ template.name }}</q-item-label>
                      </q-item-section>
                    </q-item>
                  </q-card-section>
                  <q-card-section>
                    <q-expansion-item expand-separator icon="wysiwyg" label="Show playbook yaml">
                      <q-input type="textarea" filled v-model="template.yaml" autogrow />
                      <q-btn color="secondary" icon="save" :loading="loading" flat
                        @click="SaveTemplate(template.yaml)">Save</q-btn>
                    </q-expansion-item>

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
                  </q-card-section>
                </q-card>
                <q-card flat v-if="preview">
                  <q-card-section>
                    <q-input label="Preview" type="textarea" autogrow readonly v-model="preview" :error="!preview_valid"
                      error-message="Steps are not valid." />
                  </q-card-section>
                </q-card>
              </q-tab-panel>
            </q-tab-panels>
          </template>
        </q-splitter>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref, watch, computed, toRaw } from 'vue';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';
import JobTemplateForm from '../components/JobTemplateForm.vue';
import BreadCrumb from '../components/BreadCrumb.vue';
import { PlaybookTemplate, Schema } from '../models'
import useloadData from 'src/load-data';
import { useParamStore } from 'src/stores/ParamStore';
import FilterView from '../components/FilterView.vue';

const p_store = useParamStore();

const { loading, data, pagination, AddFilter, loadData } =
  useloadData<Array<PlaybookTemplate>>('templates/playbooks');

pagination.value.rowsPerPage = 10;

const tab = ref(''),
  splitterModel = ref(15)
const current = ref(0)

const errors = ref([]);

const preview = ref('');
const preview_valid = ref(true);
const preview_errors = ref('');

const $q = useQuasar();
const $router = useRouter();

const schema = ref({} as Schema);
const model = ref({});
const filters = ref({ search: p_store.playbook_template_id });

function updateFilters() {
  AddFilter(toRaw(filters.value));
  loadData();
}

updateFilters();

p_store.clearPlaybookTemplate();

function onSubmit() {
  loading.value = true;
  api
    .post(`templates/playbooks/${tab.value}`, model.value)
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

function onPreview() {
  loading.value = true;
  api
    .post(`templates/playbooks/${tab.value}/preview`, model.value)
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

function LoadSchema() {
  if (tab.value !== '') {
    preview.value = '';
    preview_valid.value = true;
    errors.value = []
    api
      .get(`/templates/playbooks/${tab.value}/schema`)
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

function SaveTemplate(template: string) {
  if (template !== '') {
    loading.value = true;
    api
      .post('/templates/playbooks/', {
        yaml: template,
      })
      .then((response) => {
        $q.notify({
          color: 'green-4',
          textColor: 'white',
          icon: 'cloud_done',
          position: 'top',
          message: `Submitted, template_playbook_id: ${response.data.id}`,
        });
        loading.value = false;
        LoadSchema();
      })
      .catch((error) => {
        loading.value = false;
        $q.notify({
          color: 'negative',
          position: 'top',
          message: `Creation failed: ${error.response.data}`,
          icon: 'report_problem',
        });
      });
  } else {
    $q.notify({
      color: 'red-5',
      textColor: 'white',
      icon: 'warning',
      position: 'top',
      message: 'You need to fill in everything',
    });
  }
}

watch(data, (old, new_model) => {
  if (old !== new_model) {
    if (data.value.length > 0) {
      tab.value = data.value[0].id
    } else {
      tab.value = ''
    }
  }
});

// watch(search, async (oldSearch, newSearch) => {
//   AddFilter({ search: search.value });
//   loadData();
// });

watch(tab, (old, new_model) => {
  if (old !== new_model) {
    LoadSchema();
  }
});

const pages = computed(() =>
  Math.ceil(pagination.value.rowsNumber / pagination.value.rowsPerPage)
);

watch(current, (old_value, new_value) => {
  if (old_value !== new_value) {
    pagination.value.page = current.value;
    loadData();
  }
});

</script>
