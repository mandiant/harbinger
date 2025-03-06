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
    <q-select :label="name" clearable v-model="selected" :options="selectedOptions" option-label="name" :multiple="multiple"
      @update:model-value="updateValue" :readonly="readonly" borderless dense options-dense style="min-width: 150px"
      @filter="filterFn" use-input input-debounce="0">
      <template v-slot:option="{ itemProps, opt, selected, toggleOption }">
        <q-item v-bind="itemProps">
          <q-item-section v-if="opt.color" :style="{ background: opt.color }" :text-color="calcColor(opt)">
            <q-btn flat :style="{ background: opt.color }" :text-color="calcColor(opt)">
              {{ opt.name }} ({{ opt.count }})
            </q-btn>
          </q-item-section>
          <q-item-section v-else :class="$q.dark.isActive ? 'text-white' : 'text-black'">
            {{ opt.name }} ({{ opt.count }})
          </q-item-section>
          <q-item-section side v-if="multiple">
            <q-toggle :model-value="selected" @update:model-value="toggleOption(opt)" />
          </q-item-section>
        </q-item>
      </template>
    </q-select>
  </div>
</template>

<script setup lang="ts">
import { toRefs, ref, Ref } from 'vue';
import { FilterOption } from '../models';


const emit = defineEmits(['update:modelValue']);

const props = defineProps({
  modelValue: {
    type: [String, Array<string>],
    default: '',
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  multiple: {
    type: Boolean,
    default: true,
  },
  options: {
    type: Array<FilterOption>,
    required: true,
  },
  name: {
    type: String,
    required: true,
  }
});


const { modelValue, readonly, multiple, options } = toRefs(props);

const selected: Ref<Array<FilterOption> | FilterOption | null> = ref(multiple.value? [] : null);


const selectedOptions = ref([])
selectedOptions.value = options.value

if(typeof modelValue.value === 'string'){
  if(modelValue.value !== '') {
    if(!multiple.value){
      modelValue.value.split(',').forEach((element) => {
        selected.value = { name: element } as FilterOption
      })
    } else if (modelValue.value !== null) {
      modelValue.value.split(',').forEach((element) => {
        selected.value.push({ name: element } as FilterOption)
      })
    }
  }
} else if (Array.isArray(modelValue.value)) {
  modelValue.value.forEach((element) => {
    if(!multiple.value){
        selected.value = { name: element } as FilterOption
      } else if (modelValue.value !== null) {
        selected.value.push({ name: element } as FilterOption)
      }
  })
}

function filterFn(val: string, update) {
  if (val === '') {
    update(() => {
      selectedOptions.value = options.value
    })
    return
  }

  update(() => {
    const needle = val.toLowerCase()
    selectedOptions.value = options.value.filter(v => v.name.toLowerCase().indexOf(needle) > -1)
  })
}

// from https://stackoverflow.com/a/12043228
function calcColor(filter: FilterOption) {
  var c = filter.color.substring(1);      // strip #
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

function updateValue(event: FilterOption) {
  if (multiple.value) {
    if (event !== null) {
      let result: string[] = [];
      selected.value.forEach((element) => {
        result.push(element.name)
      })
      emit('update:modelValue', result);
    } else {
      emit('update:modelValue', []);
    }
  } else {
    if (event !== null) {
      emit('update:modelValue', event.name);
    } else {
      emit('update:modelValue', event);
    }
  }
}
</script>
