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
    <q-select :label="label" filled v-model="selected" :options="filteredLabels" option-label="name" :multiple="multiple"
      @update:model-value="updateValue" :readonly="readonly" borderless dense options-dense style="min-width: 150px" />
  </div>
</template>

<script setup lang="ts">
import { Label } from 'src/models';
import { useLabelStore } from 'src/stores/labels';
import { toRefs, ref, computed } from 'vue';
const label_store = useLabelStore();

const emit = defineEmits(['update:modelValue']);

const props = defineProps({
  modelValue: {
    type: Array<Label>,
    required: true
  },
  label: {
    type: String,
    required: true
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  multiple: {
    type: Boolean,
    default: true,
  },
  category: {
    type: String,
    default: '',
  }
});

const selected = ref([]);

const { label, readonly, multiple, category } = toRefs(props);

const filteredLabels = computed(() => {
  return label_store.labels.filter((entry) => {
    return entry.category === category.value || category.value === ''
  })
})

function updateValue(event: Array<Label>) {
  if (multiple.value) {
    if (event !== null) {
      let result: string[] = [];
      event.forEach((element) => {
        result.push(element.id)
      })

      emit('update:modelValue', result);
    } else {
      emit('update:modelValue', []);
    }
  } else {
    if (event !== null) {
      emit('update:modelValue', selected.value.id);
    }
  }
}
</script>
