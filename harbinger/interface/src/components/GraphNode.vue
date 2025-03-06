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
  <q-card flat class="col-2">
    <scroll-object :object="object" v-if="object.name" />
    <q-card-section>
      <q-inner-loading :showing="loading">
        <q-spinner-gears size="50px" color="secondary" />
      </q-inner-loading>
    </q-card-section>
    <q-card-actions>
      <q-btn
        @click="markOwned(object.name, loadObject)"
        v-if="!object.owned"
        icon="fas fa-skull"
        label="Mark as owned"
        color="secondary"
      />
      <q-btn
        @click="unmarkOwned(object.name, loadObject)"
        v-if="object.owned"
        icon="fas fa-skull"
        label="Unmark as owned"
        color="secondary"
      />
    </q-card-actions>
  </q-card>
</template>

<script setup lang="ts">
import { toRefs } from 'vue';
import { Node } from '../models';
import useLoadObject from 'src/load-object';
import useMark from 'src/mark-owned';
import ScrollObject from './ScrollObject.vue';

const props = defineProps({
  objectid: {
    type: String,
    default: '',
  },
});

const { objectid } = toRefs(props);
const { loading, object, loadObject } = useLoadObject<Node>(
  'graph/nodes',
  objectid.value
);

const { markOwned, unmarkOwned } = useMark();

loadObject();
</script>
