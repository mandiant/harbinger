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
  <q-list class="container" style="min-height: 400px">
    <q-scroll-area class="fit">
      <q-item clickable v-ripple v-for="entry in filtered_object" v-bind:key="entry[0]">
        <q-item-section @click="copyToClipboard(entry[1])" v-if="entry[0]">
          <q-item-label overline>{{ entry[0] }}</q-item-label>
          <q-item-label>{{ entry[1] }}</q-item-label>
        </q-item-section>
      </q-item>
    </q-scroll-area>
  </q-list>
</template>

<style scoped>
.container {
  height: calc(100% - 95px);
}
</style>

<script setup lang="ts">
import { toRefs, computed } from 'vue';
import { copyToClipboard } from 'quasar'
const props = defineProps({
  object: {
    type: Object,
    required: true,
  },
  filter_keys: {
    type: Array<string>,
    default: [],
  },
});
const { object, filter_keys } = toRefs(props);

const filtered_object = computed(() => {
  var result = Object.keys(object.value)
    .filter((key) => !filter_keys.value.includes(key))
    .filter((key) => object.value[key])
    .map((key) => [key, object.value[key]]);
  return result;
});
</script>
