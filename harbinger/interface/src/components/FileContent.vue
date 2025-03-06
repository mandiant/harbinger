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
  <monaco-editor v-model="object.text" v-if="object.text && highlights_loaded" :readonly="true" language="text" :highlights="highlight_text"/>
</template>

<script setup lang="ts">
import { toRefs, ref, computed } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { Highlight } from 'src/models';
import MonacoEditor from './MonacoEditor.vue';


const props = defineProps({
  file_id: {
    type: String,
    required: true,
  },
});

interface FileContent {
  text: string;
}


const { file_id } = toRefs(props);
const $q = useQuasar();
const loading = ref(false);
const object = ref<FileContent>({} as FileContent);

const highlights = ref<Array<Highlight>>([]);

const highlight_text = computed(() => {
  let result: Array<string> = [];

  highlights.value.forEach(element => {
    result.push(element.hit);
  });

  return Array.from(new Set(result));
});

function loadObject() {
  loading.value = true;
  api
    .get(`/files/${file_id.value}/content`)
    .then((response) => {
      object.value = response.data;
      loading.value = false;
    })
    .catch((error) => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: `Loading failed: ${error.message}`,
        icon: 'report_problem',
      });
    });
}
loadObject();

const highlights_loaded = ref(false);

function loadHighlights() {
  api.get('/highlights/', { params: { file_id: file_id.value } }).then((response) => {
    highlights.value = response.data.items;
    highlights_loaded.value = true;
  }).catch((error) => {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: `Loading failed: ${error.message}`,
      icon: 'report_problem',
    });
  })
}

loadHighlights()

</script>
