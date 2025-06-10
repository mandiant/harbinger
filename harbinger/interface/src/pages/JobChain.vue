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
    <div class="q-pa-md row q-gutter-md">
      <q-card flat class="col-8">
        <q-card-section>
          <q-item>
            <q-item-section>
              <q-item-label>Playbook {{ id }}</q-item-label>
              <q-item-label caption>{{ playbook.status }}</q-item-label>
            </q-item-section>
            <q-item-section side top>
              <q-icon name="wifi" color="green" size="1em" v-if="connected">
                <q-tooltip>Event websocket is connected</q-tooltip>
              </q-icon>
              <q-icon name="close" color="red" size="1em" v-else />
            </q-item-section>
          </q-item>
          <q-form @submit="onSave" class="q-gutter-md">
            <q-input label="Name" v-model="playbook.playbook_name" filled />
            <q-input label="Description" v-model="playbook.description" filled />
            <q-btn label="Save" icon="save" type="submit" color="secondary" :loading="loading" />
            <q-btn v-if="playbook.status === 'created' && playbook.correct" @click="start" :loading="loading"
              icon="play_arrow" color="secondary">
              Start playbook
            </q-btn>
            <q-btn @click="debounced_load()" icon="refresh" color="secondary">
              Refresh
            </q-btn>
            <q-btn @click="createTemplate()" icon="library_add" color="secondary">
              Get template
            </q-btn>
            <q-btn @click="Clone()" icon="file_copy" color="secondary">
              Clone this playbook
            </q-btn>
            <q-btn @click="Detections()" icon="radar" color="secondary">
              Check detections
            </q-btn>
            <labels-list object-type="playbook" :object-id="String(playbook.id)" v-model="playbook.labels" />
          </q-form>
        </q-card-section>
      </q-card>
    </div>

    <q-dialog v-model="showDialog">
      <q-card style="min-width: 80vw; max-width: 80vw;">
        <q-card-section>
          <div class="text-h6">Template</div>
        </q-card-section>
        <q-card-section>
          <monaco-editor v-model="template" :readonly="true" language="yaml" />
        </q-card-section>
        <q-card-actions>
          <q-btn color="primary" label="OK" @click="showDialog = false" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-banner inline-actions class="text-white bg-secondary" v-if="playbook.correct === false">
      The graph has a cycle, fix this before starting.
    </q-banner>

    <q-card flat>
      <q-card-section>
        <div class="text-h6">Playbook Steps</div>
      </q-card-section>
      <q-tabs v-model="tab" dense class="text-grey" active-color="primary" indicator-color="primary" align="justify"
        narrow-indicator>
        <q-tab name="nodes" label="Nodes view" :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
        <q-tab name="graph" label="Graph view" :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
      </q-tabs>
    </q-card>
    <q-separator />
    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="nodes">
        <div class="q-pa-md row items-center q-gutter-md">
          <template v-for="step in data" v-bind:key="step.id">
            <q-card class="col-auto">
              <q-linear-progress :value="100" rounded color="positive" class="q-mt-sm"
                v-if="step.status === 'completed'" />
              <q-linear-progress :value="100" rounded color="negative" class="q-mt-sm"
                v-else-if="step.status === 'error'" />
              <q-linear-progress indeterminate rounded color="accent" class="q-mt-sm"
                v-else-if="step.status !== 'created'" />
              <q-card-section>
                <div class="text-h6">Step {{ step.label }}</div>
                <div class="text-subtitle2">
                  {{ step.status }}
                  <q-spinner-hourglass color="primary" v-if="step.status === 'queued'" />
                  <q-spinner-hourglass color="primary" v-else-if="step.status === 'scheduled'" />
                  <q-spinner-gears color="primary" v-else-if="step.status === 'running'" />
                  <q-spinner-gears color="primary"
                    v-else-if="step.status === 'processed, waiting for more messages...'" />
                  <q-spinner-gears color="primary" v-else-if="step.status === 'processed'" />
                  <q-spinner-gears color="primary" v-else-if="step.status === 'processing'" />
                  <q-spinner-gears color="primary" v-else-if="step.status === 'submitted'" />
                  <q-icon name="check" color="green" v-else-if="step.status === 'completed'" />
                  <q-icon name="close" color="red" v-else-if="step.status === 'error'" />
                  <div v-else-if="step.status === 'created'"></div>
                  <q-icon name="question_mark" color="accent" v-else />
                </div>
              </q-card-section>
              <q-card-section>
                <q-expansion-item expand-separator icon="settings"
                      caption="Settings">

                <div class="row-equal-width">
                  <div class="row">
                    <div class="col">
                      <q-input v-model="step.label" label="the step label" readonly />
                    </div>
                    <div class="col">
                      <q-input v-model="step.depends_on" label="depends on" :disable="readonly" />
                    </div>
                    <div class="col">
                      <delay-select v-model="step.delay" :disable="readonly" />
                    </div>
                  </div>
                  <div class="row">
                    <div class="col">
                      <playbook-step-modifiers v-model="step.step_modifiers" :playbook-step-id="step.id"
                        v-on:refresh="loadData" :readonly="readonly" />
                    </div>
                  </div>
                  <div class="row" v-if="!readonly">
                    <q-dialog v-model="step.modal">
                      <q-card style="width: 700px; max-width: 80vw">
                        <q-card-section>
                          <div class="q-pa-md">
                            <div class="q-gutter-md row items-start">
                              <q-date v-model="step.execute_after" mask="YYYY-MM-DDTHH:mm:ss" color="purple" />
                              <q-time v-model="step.execute_after" mask="YYYY-MM-DDTHH:mm:ss" color="purple"
                                format24h />
                            </div>
                          </div>
                        </q-card-section>
                        <q-card-actions align="right">
                          <q-btn flat label="clear" @click="step.execute_after = null" />
                          <q-btn flat label="close" v-close-popup />
                        </q-card-actions>
                      </q-card>
                    </q-dialog>
                    <q-btn flat label="Save" icon="save" v-if="!readonly" @click="saveStep(step)" color="secondary" />
                  </div>
                </div>
                </q-expansion-item>
              </q-card-section>
              <proxy-job :readonly="readonly" v-if="step.proxy_job_id" :job_id="step.proxy_job_id"
                @delete="onDelete(step.id)" @clone="clone(step.id)" :key="proxyReloadKey" />
              <c2-job v-else-if="step.c2_job_id" :dialog="true" :readonly="readonly" :job_id="step.c2_job_id"
                @delete="onDelete(step.id)" @clone="clone(step.id)" :key="c2ReloadKey" />
              <empty-chain-step :step="step" v-on:refresh="loadData" @delete="onDelete(step.id)"
                v-else-if="!readonly"/>
            </q-card>
          </template>
          <q-btn icon="add" @click="addStep()" color="secondary" v-if="!readonly" />
        </div>
        <div class="column items-center">
          <q-pagination v-model="current" direction-links :max="pages" flat color="grey" active-color="primary" />
        </div>
      </q-tab-panel>
      <q-tab-panel name="graph"><chain-steps-graph :graph="playbook.graph" /></q-tab-panel>
    </q-tab-panels>
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="100px" color="secondary" />
    </q-inner-loading>
  </q-page>
</template>

<style scoped lang="sass">
.row-equal-width
  .row > div
    padding: 10px 15px
  .row + .row
    margin-top: 1rem
</style>


<script setup lang="ts">
import { api } from 'boot/axios';
import { ref, toRefs, computed, onUnmounted, watch } from 'vue';
import { useQuasar, debounce } from 'quasar';
import { Chain, ChainStep } from '../models';
import ProxyJob from '../components/ProxyJob.vue';
import EmptyChainStep from '../components/EmptyChainStep.vue';
import C2Job from '../components/C2Job.vue';
import BreadCrumb from '../components/BreadCrumb.vue';
import useloadData from 'src/load-data';
import ChainStepsGraph from '../components/ChainStepsGraph.vue';
import PlaybookStepModifiers from 'src/components/PlaybookStepModifiers.vue';
import DelaySelect from 'src/components/DelaySelect.vue';
import MonacoEditor from 'src/components/MonacoEditor.vue';
import { useRouter, useRoute } from 'vue-router';
import LabelsList from 'src/components/LabelsList.vue';
import { defineTypedStore } from 'src/stores/datastore';
import { storeToRefs } from 'pinia'

const store = defineTypedStore<Chain>('playbooks')();

const $router = useRouter();
const route = useRoute();


const $q = useQuasar();
const props = defineProps({
  id: {
    type: String,
    required: true,
  }
});

const { id } = toRefs(props);
const playbook = ref<Chain>({} as Chain);
const { cache } = storeToRefs(store);

const proxyReloadKey = ref(0);
const c2ReloadKey = ref(0);

watch(cache, () => {
  const test = cache.value[id.value]
  if (test) {
    playbook.value = test
  }
}, { deep: true })

store.loadById(id.value).then((item => {
  loading.value = false;
  playbook.value = item
}));

const tab = ref('nodes');
const showDialog = ref(false);
const template = ref('');

const { loading, data, pagination, loadData, AddFilter } = useloadData<
  Array<ChainStep>
>('steps');

pagination.value.rowsPerPage = 20;

AddFilter({ playbook_id: id.value })

loadData()

const debounced_load = debounce(function () {
  loadData()
  proxyReloadKey.value++
  c2ReloadKey.value++
}, 10, false)

function onSave() {
  loading.value = true;
  api
    .put(`/playbooks/${playbook.value.id}`, {
      playbook_name: playbook.value.playbook_name,
      description: playbook.value.description,
    })
    .then((response) => {
      loading.value = false
      playbook.value = response.data;
      $q.notify({
        color: 'positive',
        position: 'top',
        message: 'Updated playbook',
        icon: 'report_problem',
      });
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Updating failed',
        icon: 'report_problem',
      });
    });
}

function saveStep(step: ChainStep) {
  loading.value = true;
  api
    .put(`/steps/${step.id}`, step)
    .then((response) => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: `Updated step ${response.data.id}`,
        position: 'top',
      });
      loadData();
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Updating failed',
        icon: 'report_problem',
      });
    });
}

function addStep() {
  loading.value = true;
  api
    .post('/steps/', { playbook_id: id.value })
    .then((response) => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: `Added step ${response.data.id}`,
        position: 'top',
      });
      loadData();
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Adding failed',
        icon: 'report_problem',
      });
    });
}

function onDelete(step_id: string) {
  loading.value = true;
  api
    .delete(`/steps/${step_id}`)
    .then(() => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: `Deleted step ${step_id}`,
        position: 'top',
      });
      data.value = data.value.filter((element) => element.id != step_id)
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Deleting failed',
        icon: 'report_problem',
      });
    });
}

function clone(step_id: string) {
  loading.value = true;
  api
    .post(`/steps/${step_id}/clone`)
    .then(() => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: `Cloned step ${step_id}`,
        position: 'top',
      });
      loadData();
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Cloning failed',
        icon: 'report_problem',
      });
    });
}

const readonly = computed(() => {
  if (playbook.value !== null) {
    if (playbook.value.status === 'created') {
      return false;
    }
  }
  return true;
});


function start() {
  api
    .post(`/playbooks/${id.value}/start`)
    .then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: 'Started playbook',
        position: 'top',
      });
      loading.value = false;
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Starting failed',
        icon: 'report_problem',
      });
    });
}

function createTemplate() {
  api
    .get(`/playbooks/${id.value}/template`)
    .then((response) => {
      template.value = response.data.yaml;
      showDialog.value = true;
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Template creation failed',
        icon: 'report_problem',
      });
    });
}

function Clone() {
  api
    .post(`/playbooks/${id.value}/clone`)
    .then((response) => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        position: 'top',
        icon: 'cloud_done',
        message: 'Cloned playbook',
      });
      loading.value = false;
      $router.push({ name: 'playbook', params: { id: response.data.id } });
    })
    .catch((error) => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: `Failed to clone: ${error.response.data.error}`,
        icon: 'report_problem',
      });
    });
}

function Detections() {
  api
    .post('/suggestions/playbook_detection', { playbook_id: id.value })
    .then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        position: 'top',
        icon: 'radar',
        message: 'Started checking detections',
      });
      loading.value = false;
    })
    .catch((error) => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: `Failed to start: ${error.response.data.error}`,
        icon: 'report_problem',
      });
    });
}

const connection = ref<WebSocket>({} as WebSocket);

const connected = ref(false);

function CreateWebSocket() {
  let protocol = location.protocol.replace('http', 'ws');

  let ws_url = `${protocol}//${location.host}/playbooks/${id.value}/events`;

  if (process.env.NODE_ENV === 'development') {
    ws_url = `${protocol}//localhost:8000/playbooks/${id.value}/events`;
  }

  connection.value = new WebSocket(ws_url);

  connection.value.onmessage = function (event) {
    try {
      try {
        let value = JSON.parse(event.data);
        if (value.event === 'updated_proxy_job') {
          data.value.forEach((element: ChainStep) => {
            if (element.proxy_job_id === value.id) {
              element.proxy_job_id = '';
            }
          });
        }
      } catch (e) { }
      debounced_load();
    } catch (e) { }
  };
  connection.value.onopen = function () {
    connected.value = true;
  };
  connection.value.onclose = function () {
    connected.value = false;
  };
}

CreateWebSocket();

onUnmounted(() => {
  if (connection.value) {
    connection.value.close();
  }
});

const current = ref(1);

watch(current, (old_value, new_value) => {
  if (old_value !== new_value) {
    pagination.value.page = current.value;
    loadData();
  }
});

watch(route, () => {
  AddFilter({ playbook_id: id.value });
  loadData();
});

const pages = computed(() =>
  Math.ceil(pagination.value.rowsNumber / pagination.value.rowsPerPage)
);
</script>
