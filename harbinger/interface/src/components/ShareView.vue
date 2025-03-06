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
  <div>
    <h6>{{ object.unc_path }}</h6>
    <q-tabs v-model="tab" dense class="text-grey" active-color="primary" indicator-color="primary" align="justify"
      narrow-indicator>
      <q-tab name="list" label="List of files" :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
      <q-tab name="tree" label="Tree format" :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
    </q-tabs>

    <q-separator />

    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="list">
        <share-files :share_id="share_id" />
      </q-tab-panel>
      <q-tab-panel name="tree">
        <share-files-tree :share_id="share_id" />
      </q-tab-panel>
    </q-tab-panels>
  </div>
</template>

<script setup lang="ts">
import { toRefs, ref } from 'vue';
import ShareFiles from './ShareFiles.vue';
import ShareFilesTree from './ShareFilesTree.vue';
import useLoadObject from 'src/load-object';
import { Share } from 'src/models';

const props = defineProps({
  share_id: {
    type: String,
    required: true,
  },
});

const tab = ref('list')

const { share_id } = toRefs(props);

const { object, loadObject } = useLoadObject<Share>(
  'shares',
  share_id.value
);

loadObject()

</script>
