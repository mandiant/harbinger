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
  <q-card-section v-if="host_id">
    <q-item>
      <q-item-section avatar>
        <q-icon name="warning" />
      </q-item-section>
      <q-item-section>
        <q-item-label>
          This object is not connected to any node in neo4j. Please select an
          object below
        </q-item-label>
      </q-item-section>
    </q-item>
  </q-card-section>
  <q-card-section v-if="host_id">
    <target-computer
      v-model="model"
      return_key="objectid"
      label="Select a computer to link."
    />
  </q-card-section>
  <q-card-actions v-if="host_id">
    <q-btn label="Save" icon="save" color="secondary" @click="saveHost" />
  </q-card-actions>
</template>

<script setup lang="ts">
import { ref, toRefs } from 'vue';
import TargetComputer from './TargetComputer.vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
const $q = useQuasar();
const props = defineProps({
  host_id: {
    type: String,
    default: '',
  },
});

const { host_id } = toRefs(props);
const model = ref('');

const emit = defineEmits(['saved']);

function saveHost() {
  if (model.value) {
    api
      .put(`/hosts/${host_id.value}`, { objectid: model.value })
      .then(() => {
        emit('saved');
      })
      .catch((error) => {
        $q.notify({
          color: 'negative',
          position: 'top',
          message: `Saving failed: ${error.response.data}`,
          icon: 'report_problem',
        });
      });
  } else {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: 'Please select a node',
      icon: 'report_problem',
    });
  }
}
</script>
