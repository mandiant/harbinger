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
  <q-item clickable v-ripple v-for="entry in filtered_object" v-bind:key="entry[0]">
    <q-item-section @click="copyToClipboard(entry[1])" v-if="entry[0]">
      <q-item-label overline>{{ entry[0] }}</q-item-label>
      <q-item-label v-if="entry[0] !== 'labels' && entry[0] !== 'arguments'">
        <q-input v-model="entry[1]" autogrow readonly flat
          filled />
        </q-item-label>
      <labels-list v-else-if="entry[0] === 'labels'" :object-type="object_type" :object-id="object_id" v-model="entry[1]" />
      <pre v-else-if="entry[0] === 'arguments'">
{{ entry[1] }}
      </pre>
    </q-item-section>
  </q-item>
</template>

<script setup lang="ts">
import LabelsList from './LabelsList.vue';
import { toRefs, computed } from 'vue';
import { copyToClipboard } from 'quasar'
const props = defineProps({
  object: {
    type: Object,
    required: true,
  },
  object_id: {
    type: String,
    required: true,
  },
  object_type: {
    type: String,
    required: true,
  },
  filter_keys: {
    type: Array<string>,
    default: [],
  },
});
const { object, object_id, object_type, filter_keys } = toRefs(props);

const filtered_object = computed(() => {
  var result = Object.keys(object.value)
    .filter((key) => !filter_keys.value.includes(key))
    .filter((key) => object.value[key])
    .map((key) => [key, object.value[key]]);
  return result;
});
</script>
