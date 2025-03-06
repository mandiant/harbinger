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
      <q-linear-progress :value="100" rounded color="positive" class="q-mt-sm" v-if="job.status === 'completed'" />
      <q-linear-progress :value="100" rounded color="negative" class="q-mt-sm" v-else-if="job.status === 'error'" />
      <q-linear-progress indeterminate rounded color="accent" class="q-mt-sm" v-else-if="job.status !== 'created'" />
      <q-card-section>
        <q-item-section>
          <q-item-label>Socks job {{ id }}</q-item-label>
          <q-item-label caption :class="$q.dark.isActive ? 'text-white' : 'text-black'">{{ job.status }}</q-item-label>
        </q-item-section>
        <q-card-section>
          <q-form class="q-gutter-md">
            <q-input filled v-model="job.command" label="command" :readonly="readonly" dense />
            <q-input filled v-model="job.arguments" label="arguments" :readonly="readonly" dense />
            <socks-server-select v-model="job.socks_server_id" :readonly="readonly" />
            <q-select filled v-model="job.input_files" use-input use-chips stack-label emit-value multiple
              label="Input Files" :readonly="readonly" :options="data" option-label="filename" @filter="searchFile" />
            <proxy-select v-model="job.proxy_id" :readonly="readonly" />
            <credential-select v-model="job.credential_id" :readonly="readonly" />
            <q-input filled v-model="job.env" label="env" hint="Environment flags, separate multiple with ','"
              :readonly="readonly" dense />
            <q-toggle v-model="job.tmate" label="Use tmate" :readonly="readonly" />
            <q-toggle v-model="job.asciinema" label="Use asciinema" :readonly="readonly" />
            <q-toggle v-model="job.proxychains" label="Use proxychains" :readonly="readonly" />
            <q-btn color="secondary" icon="save" flat @click="save" v-if="!readonly">Save</q-btn>
          </q-form>
        </q-card-section>
      </q-card-section>
      <q-card-section>
        <labels-list object-type="proxy_job" :object-id="String(job.id)" v-model="job.labels" />
      </q-card-section>
      <q-card-actions>
        <q-btn v-if="job.status === 'started'" @click="kill" :loading="loading" color="secondary" icon="stop">
          Kill job
        </q-btn>
        <q-btn :to="{ name: 'playbook', params: { id: job.playbook_id } }" v-if="job.playbook_id" label="Go to playbook"
          color="secondary" />
        <q-btn icon="play_arrow" v-else-if="job.status === null || job.status === '' || job.status === 'created'
        " color="secondary" label="Start" @click="start" />
        <q-btn icon="refresh" color="secondary" @click="loadData(); loadJob()" :loading="loading">Refresh</q-btn>
      </q-card-actions>
      <q-card-section v-if="castfile == ''">
        <socks-task-output :id="id" @update="debounced_load" />
      </q-card-section>
      <q-card-section v-else>
        <cast-player :file_id="castfile" />
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { api } from 'boot/axios';
import { ref, toRefs, computed } from 'vue';
import { useQuasar } from 'quasar';
import { ProxyJob, File } from '../models';
import BreadCrumb from '../components/BreadCrumb.vue';
import CastPlayer from 'src/components/CastPlayer.vue';
import ProxySelect from 'src/components/ProxySelect.vue';
import CredentialSelect from 'src/components/CredentialSelect.vue';
import useloadData from 'src/load-data';
import SocksServerSelect from 'src/components/SocksServerSelect.vue';
import SocksTaskOutput from 'src/components/SocksTaskOutput.vue'
import { debounce } from 'quasar'
import LabelsList from 'src/components/LabelsList.vue';

const { loading, data, pagination, loadData, AddFilter } = useloadData<
  Array<File>
>('files');
pagination.value.rowsPerPage = 100;
loadData();

const $q = useQuasar();
const props = defineProps({
  id: {
    type: String,
    required: true
  },
});

const { id } = toRefs(props);

const castfile = computed(() => {
  let result = ''
  if (job.value) {
    if (job.value.files) {
      job.value.files.forEach(element => {
        if (element.filename == 'output.cast') {
          result = element.id
        }
      })
    }
  }
  return result
});

const readonly = computed(() => {
  return (job.value.status !== null && job.value.status !== '' && job.value.status !== 'created')
});

const job = ref<ProxyJob>({} as ProxyJob);

function loadJob() {
  if (id?.value !== null) {
    api
      .get(`/proxy_jobs/${id?.value}`)
      .then((response) => {
        job.value = response.data;
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
loadJob();

function kill() {
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
      loading.value = false;
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
      loading.value = false;
      loadJob();
    })
    .catch(() => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Failed to start',
        icon: 'report_problem',
      });
    });
}

function save() {
  loading.value = true;
  const files = job.value.input_files

  job.value.input_files = []
  files.forEach((element) => {
    job.value.input_files.push(element.id)
  })
  job.value.socks_server_id = job.value.socks_server.id;
  api
    .put(`/proxy_jobs/${id.value}`, job.value)
    .then((response) => {
      job.value = response.data;
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

const debounced_load = debounce(function () {
  loadData()
  loadJob()
}, 100, false)


function searchFile(val: string, update: (a: () => void) => void) {
  update(() => {
    AddFilter({ search: val })
    loadData()
  })
}
</script>
