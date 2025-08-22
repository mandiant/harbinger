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
  <div class="q-gutter-sm">
    <q-btn v-for="label in modelValue" v-bind:key="label.id" flat :label="label.name" :style="{ background: label.color }"
      :text-color="calcColor(label)">
      <q-tooltip>
        [{{ label.category }}] {{ label.name }}
      </q-tooltip>
    </q-btn>
    <q-btn v-if="!readonly" flat icon="edit" color="secondary" @click="showDialog = true" />
  </div>
  <q-dialog v-model="showDialog">
    <q-card style="width: 800px; max-width: 80vw">
      <q-card-section>
        <div class="text-h6">Edit labels</div>
      </q-card-section>
      <q-card-section class="q-gutter-sm">
        <div class="text-h6">Current labels</div>
        <q-btn v-for="label in modelValue" v-bind:key="label.id" flat :label="label.name" @click="deleteLabel(label.id)"
          icon="delete" :style="{ background: label.color }" :text-color="calcColor(label)" />
      </q-card-section>
      <q-card-section class="q-gutter-sm" v-for="[key, value] in filteredTags" v-bind:key="key">
        <div class="text-h6" v-if="key">{{ key }}</div>
        <div class="text-h6" v-else>No category</div>
        <q-btn v-for="label in filterLabels(value)" v-bind:key="label.id" flat :label="label.name" @click="addLabel(label.id)"
          icon="add" :style="{ background: label.color }" :text-color="calcColor(label)" />
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat label="close" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { Label } from '../models'
import { toRefs, ref, computed } from 'vue';
import { api } from 'boot/axios';
import { useLabelStore } from 'src/stores/labels';

const label_store = useLabelStore();

const $q = useQuasar();
const emit = defineEmits(['update:modelValue']);

// from https://stackoverflow.com/a/12043228
function calcColor(label: Label) {
  if (!label.color || typeof label.color !== 'string') {
    return 'black'; // Return a default color if none is provided
  }
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

const filteredTags = computed(() => {
  return label_store.label_category_map;
})

function filterLabels(labels: Array<Label>){
  return labels.filter(entry => {
    return !modelValue.value.find((el => {
      return el.id == entry.id
    }))
  })
}

// const filteredTags = computed(() => {
//   return label_store.labels.filter(entry => {
//     return !modelValue.value.find((el => {
//       return el.id == entry.id
//     }))
//   })
// })

const props = defineProps({
  modelValue: {
    type: Array<Label>,
    required: true
  },
  objectType: {
    type: String,
    required: true
  },
  objectId: {
    type: String,
    required: true
  },
  readonly: {
    type: Boolean,
    default: false,
  },
});

interface Form {
  label_id: string;
  domain_id?: string;
  password_id?: string;
  credential_id?: string;
  proxy_id?: string;
  proxy_job_id?: string;
  proxy_job_output?: string;
  file_id?: string;
  playbook_id?: string;
  playbook_step_id?: string;
  c2_job_id?: string;
  host_id?: string;
  process_id?: string;
  suggestion_id?: string;
  playbook_template_id?: string;
}

const showDialog = ref(false);

const { modelValue, objectType, objectId, readonly } = toRefs(props);

function deleteLabel(label_id: string) {
  let data: Form = {
    label_id: label_id,
  }
  data[`${objectType.value}_id`] = objectId.value
  api.delete('/item_label/', { data: data }).then(() => {
    $q.notify({
      color: 'green-4',
      textColor: 'white',
      icon: 'cloud_done',
      position: 'top',
      message: 'Deleted label',
    })
    const result = modelValue.value.filter(entry => entry.id !== label_id)
    emit('update:modelValue', result)
  }).catch(() => {
    $q.notify({
      color: 'red-5',
      textColor: 'white',
      icon: 'warning',
      position: 'top',
      message: 'Stuff',
    });
  });
}

function addLabel(label_id: string) {
  let data: Form = {
    label_id: label_id,
  }
  data[`${objectType.value}_id`] = objectId.value
  api.post('/item_label/', data).then((response) => {
    $q.notify({
      color: 'green-4',
      textColor: 'white',
      icon: 'cloud_done',
      position: 'top',
      message: 'Added label',
    })
    let list = modelValue.value
    list.push(response.data.label)
    emit('update:modelValue', list)
  }).catch(() => {
    $q.notify({
      color: 'red-5',
      textColor: 'white',
      icon: 'warning',
      position: 'top',
      message: 'Stuff',
    });
  });
}
</script>
