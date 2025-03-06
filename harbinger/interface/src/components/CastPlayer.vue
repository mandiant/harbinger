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
  <div class="q-pa-md">
    <div style="width: 50vw; max-width: 50vw" ref="player"></div>
  </div>
</template>

<script setup lang="ts">
import * as AsciinemaPlayer from 'asciinema-player';
import { api } from 'boot/axios';
import { ref, onMounted, toRefs } from 'vue'
const props = defineProps({
  file_id: {
    String,
    required: true
  }
});
const { file_id } = toRefs(props);

const player = ref(null)
const castdata = ref('')

function loadFile() {
  if(file_id.value){
    api.get(`/files/${file_id.value}/download`, { responseType: 'text' }).then((response) => {
      castdata.value = response.data
      AsciinemaPlayer.create(
        {data: castdata.value},
        player.value,
        {
          idleTimeLimit: 1,
        }
      );
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    }).catch(() => {});
  }
}

onMounted(() => {
  loadFile()
})

</script>
