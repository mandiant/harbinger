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
    <q-select
      v-model="implant"
      :option-label="(opt) => formatImplant(opt)"
      :options="implants"
      label="C2 implant"
      clearable
      @update:model-value="updateValue"
      filled
      :readonly="readonly"
      :error="!implant.id"
      lazy-rules
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, toRefs } from 'vue';
import { C2Implant } from '../models';
import { useMythicImplantStore } from 'src/stores/mythic_implants'

const store = useMythicImplantStore()

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  values: {
    type: Array<string>,
    default: [],
  }
});

const { modelValue, readonly, values } = toRefs(props);

const emit = defineEmits(['update:modelValue']);

const implants = ref<Array<C2Implant>>([]);
const implant = ref<C2Implant>({} as C2Implant);

function updateValue(event: C2Implant) {
  if (event !== null) {
    emit('update:modelValue', event.id);
  } else {
    emit('update:modelValue', null);
  }
}

function formatImplant(obj: C2Implant) {
  if (obj.id) {
    let host = `${obj.username}@${obj.hostname}`
    if(obj.domain){
      host = `${obj.domain}/` + host
    }
    let splitted = obj.process.split('\\')
    let process = splitted[splitted.length - 1]
    return `[${obj.payload_type}] [${obj.pid}:${process}] ${host}`;
  }
  return '';
}

async function loadSpecificValues() {
  if(!readonly.value){
    values.value.forEach(async implant => {
      const impl = await store.loadImplant(implant)
      if (impl) {
        implants.value.push(impl)
      }
    })
  }
}

if(values.value.length === 0){
  implants.value = store.aliveImplants
} else {
  loadSpecificValues()
}

async function loadDefault() {
  if (modelValue.value) {
    const result = await store.loadImplant(modelValue.value)
    if(result){
      implant.value = result
    }
  }
}
loadDefault();

watch(modelValue, (old, new_model) => {
  if (old !== new_model) {
    loadDefault();
  }
  if (!modelValue.value) {
    implant.value = {} as C2Implant;
  }
});
</script>
