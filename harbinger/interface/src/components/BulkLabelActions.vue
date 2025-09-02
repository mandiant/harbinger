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
    <q-btn-dropdown color="primary" dense :disable="selected.length === 0" label="Actions" icon="apps">
      <q-list>
        <q-item clickable v-close-popup @click="showAddDialog = true">
          <q-item-section avatar>
            <q-icon name="label" color="secondary" />
          </q-item-section>
          <q-item-section>Add Label</q-item-section>
        </q-item>
        <q-item clickable v-close-popup @click="showRemoveDialog = true">
          <q-item-section avatar>
            <q-icon name="label_off" color="negative" />
          </q-item-section>
          <q-item-section>Remove Label</q-item-section>
        </q-item>
      </q-list>
    </q-btn-dropdown>

    <q-dialog v-model="showAddDialog">
      <q-card style="width: 800px; max-width: 80vw">
        <q-card-section>
          <div class="text-h6">Add a label to {{ selected.length }} item(s)</div>
        </q-card-section>
        <q-card-section class="q-gutter-sm" v-for="[key, value] in label_store.label_category_map" v-bind:key="key">
          <div class="text-h6" v-if="key">{{ key }}</div>
          <div class="text-h6" v-else>No category</div>
          <q-btn v-for="label in value" v-bind:key="label.id" flat :label="label.name" @click="addLabel(label.id)"
            icon="add" :style="{ background: label.color }" :text-color="calcColor(label)" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="close" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <q-dialog v-model="showRemoveDialog">
      <q-card style="width: 800px; max-width: 80vw">
        <q-card-section>
          <div class="text-h6">Remove a label from {{ selected.length }} item(s)</div>
        </q-card-section>
        <q-card-section class="q-gutter-sm" v-for="[key, value] in label_store.label_category_map" v-bind:key="key">
          <div class="text-h6" v-if="key">{{ key }}</div>
          <div class="text-h6" v-else>No category</div>
          <q-btn v-for="label in value" v-bind:key="label.id" flat :label="label.name" @click="removeLabel(label.id)"
            icon="delete" :style="{ background: label.color }" :text-color="calcColor(label)" />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="close" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { useLabelStore } from 'src/stores/labels';
import { Label } from 'src/models';

const props = defineProps<{
  selected: { id: string, name?: string, filename?: string }[];
  objectType: string;
}>();

const emit = defineEmits(['update']);

const $q = useQuasar();
const showAddDialog = ref(false);
const showRemoveDialog = ref(false);

const label_store = useLabelStore();

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
  if (luma < 80) { return 'white' }
  return 'black'
}

interface Form {
  label_id: string;
  [key: string]: string;
}

function addLabel(labelId: string) {
  for (const item of props.selected) {
    const data: Form = { label_id: labelId };
    data[`${props.objectType}_id`] = item.id;

    api.post('/item_label/', data)
      .then(() => {
        $q.notify({
          color: 'positive',
          message: `Label added to ${item.name || item.filename || item.id}`,
        });
      })
      .catch(() => {
        $q.notify({
          color: 'negative',
          message: `Error adding label to ${item.name || item.filename || item.id}`,
        });
      });
  }
  emit('update');
  showAddDialog.value = false;
}

function removeLabel(labelId: string) {
  for (const item of props.selected) {
    const data: Form = { label_id: labelId };
    data[`${props.objectType}_id`] = item.id;

    api.delete('/item_label/', { data: data })
      .then(() => {
        $q.notify({
          color: 'positive',
          message: `Label removed from ${item.name || item.filename || item.id}`,
          position: 'top'
        });
      })
      .catch(() => {
        $q.notify({
          color: 'negative',
          message: `Error removing label from ${item.name || item.filename || item.id}`,
          position: 'top'
        });
      });
  }
  emit('update');
  showRemoveDialog.value = false;
}
</script>