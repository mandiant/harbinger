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
  <q-btn-dropdown stretch flat :label="`Running tasks: ${progress.length}`" v-show="progress.length > 0">
    <q-list style="min-width: 200px">
      <q-item v-for="progress, index in progress" v-bind:key="index">
        <q-item-section>
          {{ progress.description }} ({{ progress.id.substring(1, 5) }})
        </q-item-section>
        <q-item-section>
          <q-linear-progress :value="progress.percentage" size="25px" rounded color="secondary" track-color="primary">
            <div class="absolute-full flex flex-center">
              <q-badge color="white" text-color="accent" :label="(progress.percentage * 100).toFixed(2) + '%'" />
            </div>
          </q-linear-progress>
        </q-item-section>
      </q-item>
      <q-separator />
      <q-item>
        <q-item-section>
          <q-btn flat label="Clear" color="secondary" icon="delete" @click="clear"/>
        </q-item-section>
      </q-item>
    </q-list>
  </q-btn-dropdown>
</template>

<script setup lang="ts">
import { useProgressStore } from 'src/stores/progress'
import { storeToRefs } from 'pinia'
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';

const store = useProgressStore();

const { progress } = storeToRefs(store)
const $q = useQuasar();

function clear() {
  api
    .delete('/progress_bars/')
    .then(() => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        message: 'Cleared',
        position: 'top',
      });
    })
    .catch(() => {
      $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Clearing failed',
        icon: 'report_problem',
      });
    });
}
</script>
