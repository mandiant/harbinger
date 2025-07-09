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
    <q-card flat class="q-pa-md" v-if="job">
      <q-linear-progress :value="100" rounded color="positive" class="q-mt-sm" v-if="job.status === 'completed'" />
      <q-linear-progress :value="100" rounded color="negative" class="q-mt-sm" v-else-if="job.status === 'error'" />
      <q-linear-progress indeterminate rounded color="accent" class="q-mt-sm"
        v-else-if="job.status !== 'created' && job.status !== null" />
      <q-card-section>
        <q-item-section>
          <q-item-label>Socks job {{ id }}</q-item-label>
          <q-item-label caption :class="$q.dark.isActive ? 'text-white' : 'text-black'">
            {{ job.status }}
          </q-item-label>
        </q-item-section>
      </q-card-section>
      <proxy-job-component :job_id="id" :readonly="readonly" :dialog="false" @start="start" @kill="kill" :start-button="true" />
      <q-card-actions>
        <q-btn :to="{ name: 'playbook', params: { id: job.playbook_id } }" v-if="job.playbook_id" label="Go to playbook"
          color="secondary" />
      </q-card-actions>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { api } from 'boot/axios';
import { ref, toRefs, computed, watch } from 'vue';
import { useQuasar } from 'quasar';
import { ProxyJob } from '../models';
import BreadCrumb from '../components/BreadCrumb.vue';
import ProxyJobComponent from 'src/components/ProxyJob.vue';
import { defineTypedStore } from 'src/stores/datastore';

const $q = useQuasar();
const props = defineProps({
  id: {
    type: String,
    required: true
  },
});

const { id } = toRefs(props);
const loading = ref(false);

const useProxyJobStore = defineTypedStore<ProxyJob>('proxy_jobs');
const proxyJobStore = useProxyJobStore();

const job = ref<ProxyJob>();

watch(() => proxyJobStore.getItemFromCache(id.value), (newJobData) => {
  if (newJobData) {
    job.value = { ...newJobData };
  }
}, { deep: true });

const readonly = computed(() => {
  if (!job.value) return true;
  return (job.value.status !== null && job.value.status !== '' && job.value.status !== 'created')
});

async function loadJob(force = false) {
  loading.value = true;
  try {
    // Await the data and assign it directly to the local ref.
    // This ensures `job` is populated as soon as the data is available.
    const jobData = await proxyJobStore.loadById(id.value, force);
    if (jobData) {
      job.value = { ...jobData };
    }
  } catch (error) {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: 'Loading failed',
      icon: 'report_problem',
    });
  } finally {
    loading.value = false;
  }
}

watch(id, () => loadJob(), { immediate: true });

function kill() {
  loading.value = true;
  api
    .post(`/proxy_jobs/${id?.value}/kill`)
    .then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: 'Stopped job',
        position: 'top',
      });
      loadJob(true);
    })
    .catch(() => {
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Stopping job failed',
        icon: 'report_problem',
      });
    })
    .finally(() => {
      loading.value = false;
    });
}

function start() {
  loading.value = true;
  api
    .post(`/proxy_jobs/${id.value}/start`)
    .then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: 'Started job',
        position: 'top',
      });
      loadJob(true);
    })
    .catch(() => {
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Failed to start',
        icon: 'report_problem',
      });
    })
    .finally(() => {
      loading.value = false;
    });
}
</script>

