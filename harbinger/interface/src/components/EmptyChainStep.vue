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
  <span>
    <q-card-section>
      <q-btn label="Add action" @click="modal = true" icon="add" flat />
      <q-dialog v-model="modal">
        <q-card style="width: 700px; max-width: 80vw">
          <q-card-section>
            <div class="text-h6">Add an action</div>
          </q-card-section>
          <q-card-section>
            <q-tabs v-model="tab" dense class="text-grey" active-color="primary" indicator-color="primary" align="justify"
              narrow-indicator>
              <q-tab name="c2" label="C2" :class="$q.dark.isActive ? 'text-white' : 'text-black'" icon="fas fa-virus" />
              <q-tab name="proxy" label="Proxy" :class="$q.dark.isActive ? 'text-white' : 'text-black'" icon="share" />
            </q-tabs>
            <q-separator />
          </q-card-section>
          <q-tab-panels v-model="tab" animated>
            <q-tab-panel name="c2">
              <add-c2-job-template v-model="step.c2_job_id" @update:model-value="saveStep()"
                :playbook_id="step.playbook_id" />
            </q-tab-panel>
            <q-tab-panel name="proxy">
              <q-tabs v-model="tab2" dense class="text-grey" active-color="primary" indicator-color="primary"
                align="justify" narrow-indicator>
                <q-tab name="template" label="From template" :class="$q.dark.isActive ? 'text-white' : 'text-black'"
                  icon="share" />
                <q-tab name="custom" label="Custom" :class="$q.dark.isActive ? 'text-white' : 'text-black'"
                  icon="share" />
              </q-tabs>
              <q-separator />
              <q-tab-panels v-model="tab2" animated>
                <q-tab-panel name="template">
                  <add-proxy-job-template v-model="step.proxy_job_id" @update:model-value="saveStep()"
                    :playbook_id="step.playbook_id" />
                </q-tab-panel>
                <q-tab-panel name="custom">
                  <add-proxy-job v-model="step.proxy_job_id" @update:model-value="saveStep()"
                    :playbook_id="step.playbook_id" />
                </q-tab-panel>

              </q-tab-panels>
            </q-tab-panel>
          </q-tab-panels>
          <q-card-actions align="right">
            <q-btn flat label="close" v-close-popup />
          </q-card-actions>
        </q-card>
      </q-dialog>
    </q-card-section>
    <q-card-actions>
      <q-btn color="secondary" icon="delete" flat @click="emit('delete')">Delete</q-btn>
    </q-card-actions>
  </span>
</template>

<script setup lang="ts">
import { ref, toRefs } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import AddProxyJobTemplate from '../components/AddProxyJobTemplate.vue';
import AddProxyJob from './AddProxyJob.vue';
import AddC2JobTemplate from './AddC2JobTemplate.vue';
import { ChainStep } from '../models';

const $q = useQuasar();

const loading = ref(true);
const modal = ref(false);

const tab = ref('c2');
const tab2 = ref('template');

const emit = defineEmits(['refresh', 'delete']);

const props = defineProps({
  step: {
    type: Object as () => ChainStep,
    required: true,
  },
});

const { step } = toRefs(props);

function saveStep() {
  loading.value = true;
  api
    .put(`/steps/${step.value.id}`, step.value)
    .then((response) => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: `Updated step ${response.data.id}`,
        position: 'top',
      });
      emit('refresh');
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
</script>
