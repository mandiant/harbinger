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
    <c2-implants :c2_server_id="id"/>
</template>

<script setup lang="ts">
import { toRefs } from 'vue';
import C2Implants from 'src/components/C2Implants.vue';

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
});

const { id } = toRefs(props);
</script>
