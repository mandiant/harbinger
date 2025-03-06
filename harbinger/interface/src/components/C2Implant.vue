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
    <q-tab icon="details" name="implant" label="Implant details" :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
    <q-tab icon="task" name="tasks" label="Tasks" :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
    <q-tab icon="output" name="output" label="Output" :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
  </q-tabs>
  <q-separator />
  <q-tab-panels v-model="tab" animated>
    <q-tab-panel name="implant"><view-object object_type="c2_implant" :object_id="id" :object="object" /></q-tab-panel>
    <q-tab-panel name="tasks"><c2-tasks :implant_id="id" /></q-tab-panel>
    <q-tab-panel name="output"><c2-output :implant_id="id" /></q-tab-panel>
  </q-tab-panels>
</template>

<script setup lang="ts">
import { toRefs, ref } from 'vue';
import C2Tasks from './C2Tasks.vue';
import C2Output from './C2Output.vue';
import useLoadObject from 'src/load-object';
import ViewObject from './ViewObject.vue';
import { C2Implant } from 'src/models';


const props = defineProps({
  id: {
    type: String,
    required: true,
  },
});

const { id } = toRefs(props);

const { object, loadObject } = useLoadObject<C2Implant>(
  'c2/implants',
  id.value
);

loadObject()

const tab = ref('tasks')
</script>
