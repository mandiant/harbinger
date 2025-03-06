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
    <q-btn v-if="label" flat :label="label.name" :style="{ background: label.color }"
      :text-color="calcColor(label)">
      <q-tooltip>
        [{{ label.category }}] {{ label.name }}
      </q-tooltip>
    </q-btn>
</template>

<script setup lang="ts">
import { Label } from '../models'
import { toRefs, computed } from 'vue';
import { useLabelStore } from 'src/stores/labels';

const label_store = useLabelStore();

// from https://stackoverflow.com/a/12043228
function calcColor(label: Label) {
  var c = label.color.substring(1);      // strip #
  var rgb = parseInt(c, 16);   // convert rrggbb to decimal
  var r = (rgb >> 16) & 0xff;  // extract red
  var g = (rgb >> 8) & 0xff;  // extract green
  var b = (rgb >> 0) & 0xff;  // extract blue

  var luma = 0.2126 * r + 0.7152 * g + 0.0722 * b; // per ITU-R BT.709

  if (luma < 80) {
    return 'white'
  }
  return 'black'
}



const props = defineProps({
  modelValue: {
    type: String,
    required: true
  },
});


const { modelValue } = toRefs(props);

const label = computed(() =>
  label_store.getLabel(modelValue.value)
);
</script>
