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
  <q-card flat>
    <q-card-actions>
      <q-btn-dropdown class="q-ml-lg" color="secondary" label="Pre-defined queries" :loading="loading" icon="search">
        <q-list>
          <q-item clickable v-close-popup v-for="item in data" v-bind:key="item.name" @click="performQuery(item.name)">
            <q-item-section avatar>
              <q-avatar :icon="item.icon" color="secondary" text-color="white" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ item.description }}</q-item-label>
            </q-item-section>
            <q-inner-loading :showing="loading">
              <q-spinner-gears size="50px" color="primary" />
            </q-inner-loading>
          </q-item>
        </q-list>
      </q-btn-dropdown>
    </q-card-actions>
    <q-card-section>
      <chain-steps-graph :graph="graph" v-if="graph" />
    </q-card-section>

  </q-card>
</template>

<style scoped>
	.mermaid {width:200% !important}
</style>

<script setup lang="ts">
import useloadData from 'src/load-data';
import { Query } from '../models';
import { api } from 'boot/axios';
import { ref } from 'vue';
import { useQuasar } from 'quasar';
import ChainStepsGraph from '../components/ChainStepsGraph.vue'


const $q = useQuasar();
const { loading, data, pagination, loadData, onRequest, AddFilter } =
  useloadData<Array<Query>>('graph/pre-defined-queries-graph');


const graph = ref('')

loadData();


const last = ref('');

function performQuery(query: string) {
  if (query !== '') {
    last.value = query;
    loading.value = true;
    api
      .get(`/graph/pre-defined-queries-graph/${query}`, {
      })
      .then((response) => {
        loading.value = false;
        graph.value = response.data.graph;
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
</script>
