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
    
    <div class="q-pa-md row q-gutter-md">
      <graph-node :objectid="object.objectid" v-if="object.objectid" />
      <q-card flat class="col-2" v-if="!object.objectid">
        <select-graph-node :host_id="id" @saved="loadObject()" />
        <q-inner-loading :showing="loading">
          <q-spinner-gears size="50px" color="secondary" />
        </q-inner-loading>
      </q-card>
      <q-card flat class="col-8">
        <q-card-section>
          <q-item>
            <q-item-section>
              <q-item-label>Processes</q-item-label>
            </q-item-section>
          </q-item>
        </q-card-section>
        <q-card-section>
          <q-tabs v-model="tab" dense class="text-grey" active-color="primary" indicator-color="primary" align="justify"
            narrow-indicator>
            <q-tab :name="entry" :class="$q.dark.isActive ? 'text-white' : 'text-black'" :label="`Process list ${entry}`"
              v-for="(entry, key) in data" v-bind:key="key" />
          </q-tabs>

          <q-separator />
          <q-tab-panels v-model="tab" animated>
            <q-tab-panel :name="entry" v-for="(entry, key) in data" v-bind:key="key">
              <process-view :host_id="id" :number="entry" v-if="entry > 0" />
            </q-tab-panel>
          </q-tab-panels>
        </q-card-section>
        <q-inner-loading :showing="loading">
          <q-spinner-gears size="50px" color="secondary" />
        </q-inner-loading>
      </q-card>
      <q-card flat class="col-10">
        <q-card-section>
          <c2-implants :host_id="id" />
        </q-card-section>
        <q-inner-loading :showing="loading">
          <q-spinner-gears size="50px" color="secondary" />
        </q-inner-loading>
      </q-card>
      <q-card flat class="col-10">
        <q-card-section>
          <shares-list :host_id="id" />
        </q-card-section>
        <q-inner-loading :showing="loading">
          <q-spinner-gears size="50px" color="secondary" />
        </q-inner-loading>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { toRefs, ref } from 'vue';

import { Host } from '../models';
import useLoadObject from 'src/load-object';
import useLoadData from 'src/load-data';
import ProcessView from 'src/components/ProcessView.vue';
import GraphNode from 'src/components/GraphNode.vue';
import SelectGraphNode from 'src/components/SelectGraphNode.vue';
import C2Implants from 'src/components/C2Implants.vue';
import SharesList from 'src/components/SharesList.vue';


const props = defineProps({
  id: {
    type: String,
    required: true,
  },
});

const tab = ref(1);

const { id } = toRefs(props);

const { loading, object, loadObject } = useLoadObject<Host>('hosts', id.value);
const { data, loadData, AddFilter } =
  useLoadData<Array<number>>('processes/numbers');

AddFilter({ host_id: id.value });
loadData();

loadObject();
</script>
