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
  <div>Task {{ task_id }}</div>
  <div>
    <view-object :object_id="task_id" object_type="c2_task" :object="object" />
    <q-inner-loading :showing="loading">
      <q-spinner-gears size="50px" color="secondary" />
    </q-inner-loading>
  </div>
  <c2-output :task_id="task_id" />
</template>

<script setup lang="ts">
import useLoadObject from 'src/load-object';
import C2Output from './C2Output.vue';
import { toRefs } from 'vue';
import { C2Task } from 'src/models';
import ViewObject from './ViewObject.vue';

const props = defineProps({
  task_id: {
    type: String,
    required: true,
  },
});

const { task_id } = toRefs(props);

const { loading, object, loadObject } = useLoadObject<C2Task>(
  'c2/tasks',
  task_id.value
);


loadObject()


</script>
