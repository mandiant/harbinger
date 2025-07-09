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
      <q-inner-loading :showing="loading">
        <q-spinner-gears size="50px" color="secondary" />
      </q-inner-loading>
      Socks Job
      <q-form class="q-gutter-md">
        <q-input filled v-model="job.command" label="command" :readonly="readonly" dense />
        <q-input filled v-model="job.arguments" label="arguments" :readonly="readonly" dense />
        <q-select filled v-model="job.input_files" use-chips stack-label emit-value multiple label="Input Files"
          :readonly="readonly || job.status !== 'created'" :options="file_store.files" option-label="filename" />
        <proxy-select v-model="job.proxy_id" :readonly="readonly" />
        <credential-select v-model="job.credential_id" :readonly="readonly" />
        <socks-server-select v-model="job.socks_server_id" :readonly="readonly" />
        <q-input filled v-model="job.env" label="env" :readonly="readonly" dense />
        <q-toggle v-model="job.tmate" label="Use tmate" />
        <q-toggle v-model="job.asciinema" label="Use asciinema" />
        <q-toggle v-model="job.proxychains" label="Use proxychains" />
      </q-form>
    </q-card-section>
    <q-card-section>
      <labels-list object-type="proxy_job" :object-id="String(job.id)" v-model="job.labels" />
    </q-card-section>
    <q-card-actions v-show="!readonly">
      <q-btn color="secondary" icon="save" @click="save">Save</q-btn>
      <q-btn color="secondary" icon="delete" @click="emit('delete')">Delete</q-btn>
      <q-btn v-if="cloneButton" color="secondary" icon="content_copy" @click="emit('clone')">
        Clone
      </q-btn>
      <q-btn v-if="job.status === 'started'" @click="emit('kill')" :loading="loading" color="secondary" icon="stop">
        Kill job
      </q-btn>
      <q-btn icon="play_arrow" v-else-if="(job.status === null || job.status === '' || job.status === 'created') && startButton
      " color="secondary" label="Start" @click="emit('start')" />
      <q-btn icon="refresh" color="secondary" @click="loadData(job_id)" :loading="loading">Refresh</q-btn>
    </q-card-actions>
    <q-card-section v-if="job.status && !dialog">
      <q-card-section v-if="castfile == ''">
        <socks-task-output :id="job_id" />
      </q-card-section>
      <q-card-section v-else>
        <cast-player :file_id="castfile" />
      </q-card-section>
    </q-card-section>
    <q-card-section v-if="dialog">
      <q-btn flat icon="output" label="Output" @click="showDialog = true" />
    </q-card-section>
    <q-dialog v-model="showDialog">
      <q-card style="min-width: 80vw; max-width: 80vw;">
        <q-card-section class="items-center">
          <q-card-section v-if="castfile == ''">
            <socks-task-output :id="job_id" />
          </q-card-section>
          <q-card-section v-else class="column items-center">
            <cast-player :file_id="castfile" />
          </q-card-section>
        </q-card-section>
        <q-card-actions>
          <q-btn color="primary" label="OK" @click="showDialog = false" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </span>
</template>


<script setup lang="ts">
import { computed, ref, toRefs, watch } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { ProxyJob } from '../models';
import ProxySelect from '../components/ProxySelect.vue';
import CredentialSelect from '../components/CredentialSelect.vue';
import { useFileStore } from 'src/stores/files';
import CastPlayer from 'src/components/CastPlayer.vue';
import SocksTaskOutput from 'src/components/SocksTaskOutput.vue';
import SocksServerSelect from 'src/components/SocksServerSelect.vue';
import { defineTypedStore } from 'src/stores/datastore';
import LabelsList from 'src/components/LabelsList.vue';

const file_store = useFileStore();
const useProxyJobStore = defineTypedStore<ProxyJob>('proxy_jobs');
const proxyJobStore = useProxyJobStore();

const $q = useQuasar();

const loading = ref(false);

const props = defineProps({
  job_id: {
    type: String,
    required: true,
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  dialog: {
    type: Boolean,
    default: true,
  },
  startButton: {
    type: Boolean,
    default: false,
  },
  cloneButton: {
    type: Boolean,
    default: false,
  }
});
const emit = defineEmits(['delete', 'clone', 'start', 'kill']);

const { job_id, readonly, dialog, startButton, cloneButton } = toRefs(props);

// Local copy for editing
const job = ref<ProxyJob>({} as ProxyJob);

watch(() => proxyJobStore.getItemFromCache(job_id.value), (newJobData) => {
  if (newJobData) {
    job.value = { ...newJobData };
  }
}, { deep: true });

const showDialog = ref(false);
const castfile = computed(() => {
  let result = ''
  if (job.value && job.value.files) {
    job.value.files.forEach(element => {
      if (element.filename == 'output.cast') {
        result = element.id
      }
    })
  }
  return result
});


function save() {
  loading.value = true;
  // Create a deep copy to avoid modifying the local state directly before saving.
  const jobToSave = JSON.parse(JSON.stringify(job.value));

  // The API expects an array of IDs, not file objects.
  if (jobToSave.input_files && Array.isArray(jobToSave.input_files)) {
    jobToSave.input_files = jobToSave.input_files.map(file =>
      (typeof file === 'object' && file !== null && file.id) ? file.id : file
    );
  }

  api
    .put(`/proxy_jobs/${job_id.value}`, jobToSave)
    .then((response) => {
      // Update the central store with the new data from the server.
      // The watcher will then update our component's local `job` ref.
      proxyJobStore.updateObject(response.data);
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        message: 'Updated',
        position: 'top',
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

async function loadData(id: string) {
  if (id) {
    loading.value = true;
    try {
      // Fetch data using the store's caching mechanism.
      job.value = await proxyJobStore.loadById(id, true);
    } catch {
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
}

// When the job_id prop changes, load the new job's data.
watch(job_id, loadData, { immediate: true });
</script>
