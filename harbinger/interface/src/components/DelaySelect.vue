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
        <div class="row-equal-width">
            <div class="row">
                <div class="col">
                    <q-input type="number" v-model="delay_number" label="Delay" />
                </div>
                <div class="col">
                    <q-select label="Units" v-model="delay_unit" :options="options" />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { toRefs, computed } from 'vue';
const props = defineProps({
    modelValue: {
        required: false,
        type: String
    },
})

interface Entry {
    label: string;
    value: string;
}

const options: Array<Entry> = [
    { label: 'Seconds', value: 'S' },
    { label: 'Minutes', value: 'M' },
    { label: 'Hours', value: 'H' },
]

const { modelValue } = toRefs(props);
const emit = defineEmits(['update:modelValue']);

const delay_number = computed({
    get() {
        if (modelValue.value) {
            return Number(modelValue.value.slice(2, modelValue.value.length - 1))
        }
        return 0
    },
    set(newValue) {
        emit('update:modelValue', `PT${newValue}${delay_unit.value.value}`);
    }
})

const delay_unit = computed({
    get(): Entry {
        if (modelValue.value) {
            const value = modelValue.value.slice(modelValue.value.length - 1, modelValue.value.length)
            let results = options.filter((element) => {
                return element.value === value;
            })
            if (results) {
                return results[0]
            }
        }
        return options[0]
    },
    set(newValue: Entry) {
        emit('update:modelValue', `PT${delay_number.value}${newValue.value}`);
    }
})

</script>