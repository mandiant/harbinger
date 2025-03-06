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
  <q-tabs v-model="tab" dense class="text-grey" active-color="primary" indicator-color="primary" align="justify"
    narrow-indicator>
    <q-tab icon="output" name="content" label="Content" :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
    <q-tab icon="details" name="file" label="File details"
      :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
    <q-tab icon="task" name="parser_results" label="Parser results" :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
  </q-tabs>
  <q-separator />
  <q-tab-panels v-model="tab" animated>
    <q-tab-panel name="content"><file-content :file_id="file_id" /></q-tab-panel>
    <q-tab-panel name="file"> <view-object object_type="file" :object_id="file_id" :object="object" />
    </q-tab-panel>
    <q-tab-panel name="parser_results"><parser-results :file_id="file_id" /></q-tab-panel>
  </q-tab-panels>

</template>

<script setup lang="ts">
import { toRefs, ref } from 'vue';
import useLoadObject from 'src/load-object';
import ViewObject from './ViewObject.vue';
import FileContent from './FileContent.vue';
import ParserResults from './ParserResults.vue'


const props = defineProps({
  file_id: {
    type: String,
    required: true,
  },
});

const tab = ref('content')

const { file_id } = toRefs(props);
const { object, loadObject } = useLoadObject<File>(
  'files',
  file_id.value
);

loadObject()
</script>
