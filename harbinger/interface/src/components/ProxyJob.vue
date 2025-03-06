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
        <socks-server-select v-model="job.socks_server_id" :readonly="readonly"/>
        <q-input filled v-model="job.env" label="env" :readonly="readonly" dense />
        <q-toggle v-model="job.tmate" label="Use tmate" />
        <q-toggle v-model="job.asciinema" label="Use asciinema" />
        <q-toggle v-model="job.proxychains" label="Use proxychains" />
      </q-form>
    </q-card-section>
    <q-card-actions v-show="!readonly">
      <q-btn color="secondary" icon="save" flat @click="save">Save</q-btn>
      <q-btn color="secondary" icon="delete" flat @click="emit('delete')">Delete</q-btn>
      <q-btn color="secondary" icon="content_copy" flat @click="emit('clone')">
        Clone
      </q-btn>
    </q-card-actions>
    <q-card-section v-if="job.status !== 'created' && !dialog">
      <q-card>
        <q-card-section class="items-center">
          <q-card-section v-if="castfile == ''">
            <socks-task-output :id="job_id" />
          </q-card-section>
          <q-card-section v-else>
            <cast-player :file_id="castfile" />
          </q-card-section>
        </q-card-section>
        <q-card-actions>
          <q-btn color="primary" label="OK" @click="showDialog = false" />
        </q-card-actions>
      </q-card>
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
import { computed, ref, toRefs } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { ProxyJob } from '../models';
import ProxySelect from '../components/ProxySelect.vue';
import CredentialSelect from '../components/CredentialSelect.vue';
import { useFileStore } from 'src/stores/files';
import CastPlayer from 'src/components/CastPlayer.vue';
import SocksTaskOutput from 'src/components/SocksTaskOutput.vue';
import SocksServerSelect from 'src/components/SocksServerSelect.vue';


const file_store = useFileStore();

const $q = useQuasar();

const loading = ref(true);

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
  }
});
const emit = defineEmits(['delete', 'clone']);

const { job_id, readonly, dialog } = toRefs(props);
const job = ref<ProxyJob>({} as ProxyJob);
const showDialog = ref(false);
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


function save() {
  loading.value = true;
  const files = job.value.input_files

  job.value.input_files = []
  files.forEach((element) => {
    job.value.input_files.push(element.id)
  })
  api
    .put(`/proxy_jobs/${job_id.value}`, job.value)
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

function loadData() {
  if (job_id.value) {
    loading.value = true;
    api
      .get(`/proxy_jobs/${job_id?.value}`)
      .then((response) => {
        job.value = response.data;
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
}
loadData();
</script>
