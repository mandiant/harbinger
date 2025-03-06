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
  <q-list dense padding>
    <q-expansion-item expand-separator icon="bolt" :label="name"
      caption="Change tasks based on output of previous tasks">
      <q-item dense padding>
        <q-item-section top class="col-3 gt-sm">
          <q-item-label class="q-mt-sm">Output of step</q-item-label>
        </q-item-section>
        <q-item-section top class="col-3 gt-sm">
          <q-item-label class="q-mt-sm">Regex</q-item-label>
        </q-item-section>
        <q-item-section top class="col-3 gt-sm">
          <q-item-label class="q-mt-sm">Output path</q-item-label>
        </q-item-section>
        <q-item-section top class="col-3 gt-sm"  v-if="!readonly">
          <q-item-label class="q-mt-sm">Actions</q-item-label>
        </q-item-section>
      </q-item>
      <q-item dense padding v-for="entry in modelValue" v-bind:key="entry.id">
        <q-item-section top class="col-3 gt-sm">
          <q-item-label class="q-mt-sm">{{ entry.input_path }}</q-item-label>
        </q-item-section>
        <q-item-section top class="col-3 gt-sm">
          <q-item-label class="q-mt-sm">{{ entry.regex }}</q-item-label>
        </q-item-section>
        <q-item-section top class="col-3 gt-sm">
          <q-item-label class="q-mt-sm">{{ entry.output_path }}</q-item-label>
        </q-item-section>
        <q-item-section top class="col-3 gt-sm" v-if="!readonly">
          <q-btn flat label="Delete" icon="delete" color="secondary" @click="deleteModifier(entry)" />
        </q-item-section>
      </q-item>
      <q-item clickable v-ripple  v-if="!readonly">
        <q-item-section>
          <q-btn flat label="Add" icon="add" color="secondary" @click="showDialog = true" />
        </q-item-section>
      </q-item>
    </q-expansion-item>
  </q-list>
  <q-dialog v-model="showDialog">
    <q-card style="min-width: 80vw; max-width: 80vw;">
      <q-card-section>
        <q-form @submit="createModifier" @reset="resetModifier" class="q-gutter-md">
          <h5>Create a new modifier</h5>
          <q-input filled v-model="form.input_path" hint="For example: A or B, this step should (indirectly) depend on that step" label="Output of step"
            :rules="[(val: string) => !!val || 'Field is required']" />

          <q-input filled v-model="form.regex" label="Optional regex to filter the output of that step" />

          <q-input filled v-model="form.output_path" hint="For example: arguments/path" label="Output path"
            :rules="[(val: string) => !!val || 'Field is required']" />

          <div>
            <q-btn label="Submit" type="submit" color="secondary" :loading="loading" />
            <q-btn label="Reset" type="reset" color="secondary" flat class="q-ml-sm" />
            <q-btn label="Close" color="secondary" flat class="q-ml-sm" @click="showDialog = false"/>
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { toRefs, ref, computed } from 'vue';
import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
import { PlaybookStepModifier } from '../models';
const props = defineProps({
  modelValue: {
    type: Array<PlaybookStepModifier>,
    required: true,
  },
  playbookStepId: {
    type: String,
    required: true
  },
  readonly: {
    type: Boolean,
    default: false,
  }
});

const name = computed(() => 
  modelValue.value.length === 1 ? '1 Modifier': `${modelValue.value.length} Modifiers`
);

const $q = useQuasar();

const showDialog = ref(false);
const loading = ref(false);

interface Form {
  regex: string;
  input_path: string;
  output_path: string;
  output_format: string;
  on_error: string;
  playbook_step_id: string;
}

const form = ref({} as Form)

const { modelValue, playbookStepId } = toRefs(props);

const emit = defineEmits(['update:modelValue', 'refresh']);

function deleteModifier(row: PlaybookStepModifier) {
  loading.value = true;
  api.delete(`/step_modifiers/${row.id}`).then(() => {
    $q.notify({
      color: 'green-4',
      textColor: 'white',
      icon: 'cloud_done',
      position: 'top',
      message: 'Deleted modifier',
    })
    emit('refresh')
  }).catch(() => {
    $q.notify({
      color: 'red-5',
      textColor: 'white',
      icon: 'warning',
      position: 'top',
      message: 'Unable to delete modifier',
    });
    loading.value = false;
  });

}

function createModifier() {
  form.value.playbook_step_id = playbookStepId.value
  loading.value = true;
  api.post('/step_modifiers/', form.value).then(() => {
    $q.notify({
      color: 'green-4',
      textColor: 'white',
      icon: 'cloud_done',
      position: 'top',
      message: 'Added modifier',
    })
    loading.value = false;
    emit('refresh')
    showDialog.value = false;
  }).catch(() => {
    $q.notify({
      color: 'red-5',
      textColor: 'white',
      icon: 'warning',
      position: 'top',
      message: 'Stuff',
    });
    loading.value = false;
  });
}

function resetModifier() {
  form.value = {} as Form;
}

</script>
