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
  <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md" v-if="schema">
    <div>{{ schema.description }}</div>
    <span v-for="(value, key) in schema.properties" v-bind:key="key">
      <component v-if="getComponentForKey(key, value)" :is="getComponentForKey(key, value)" v-model="model[key]"
        :title="value.title" :error="!isValid(key)" :label="value.title" :options="value.enum || []" filled
        :default="value.default" :type="value.type === 'integer' ? 'number' : 'string'" />
    </span>
    <q-btn label="Preview" v-if="show_preview_button" color="secondary" @click="preview" />
    <q-btn label="Submit" type="submit" color="secondary" :loading="loading" />
    <q-btn label="Reset" type="reset" color="secondary" flat class="q-ml-sm" />
  </q-form>
</template>

<script setup lang="ts">
import { toRefs, watch, reactive } from 'vue';
import CredentialSelect from '../components/CredentialSelect.vue';
import FileSelect from '../components/FileSelect.vue';
import ProxySelect from '../components/ProxySelect.vue';
import TargetComputer from '../components/TargetComputer.vue';
import TargetDomainController from './TargetDomainController.vue';
import TargetUser from '../components/TargetUser.vue';
import TargetGroup from '../components/TargetGroup.vue';
import C2ImplantSelect from '../components/C2ImplantSelect.vue';
import SocksServerSelect from './SocksServerSelect.vue';
import KerberosSelect from './KerberosSelect.vue'
import { KeyStringValue, Schema, Property } from 'src/models';
import { QInput, QSelect, QToggle } from 'quasar';

const getComponentForKey = (key: string | number, value: Property) => {
  // keep the type checking happy.
  if (typeof key === 'number') {
    return null;
  }
  if (key.startsWith('target_computer')) return TargetComputer;
  if (key.startsWith('target_domain_controller')) return TargetDomainController;
  if (key.startsWith('c2_implant')) return C2ImplantSelect;
  if (key.startsWith('target_group')) return TargetGroup;
  if (key.startsWith('target_user')) return TargetUser;
  if (key.startsWith('credential_id')) return CredentialSelect;
  if (key.startsWith('kerberos_id')) return KerberosSelect;
  if (key.startsWith('file_id')) return FileSelect;
  if (key.startsWith('socks_server')) return SocksServerSelect;
  if (key === 'playbook_id') return null;
  if (key.startsWith('proxy_id')) return ProxySelect;
  if (value.enum && value.enum.length > 0) return QSelect;
  if (value.type === 'string') return QInput;
  if (value.type === 'integer') return QInput;
  if (value.type === 'boolean') return QToggle;
  return null; // Or a default component if no match is found
};


const emit = defineEmits(['update:modelValue', 'submit', 'preview']);


const props = defineProps<{
  modelValue: KeyStringValue;
  schema: Schema;
  loading: boolean;
  show_preview_button: boolean;
}>();

const { schema, loading, show_preview_button } = toRefs(props);

const model = reactive({} as KeyStringValue);

function isValid(key: string | number) {
  // keep the type checking happy.
  if (typeof key === 'number') {
    return true;
  }
  if (props.schema && props.schema.required) {
    if (props.schema.required.includes(key)) {
      if (key in model) {
        if (model[key].length > 0) {
          return true;
        }
      }
      return false;
    }
  }
  return true;
}

function onSubmit() {
  emit('submit');
}

function preview() {
  emit('preview');
}

watch(model, async (old, new_model) => {
  emit('update:modelValue', new_model);
});

watch(
  () => props.schema,
  async () => {
    for (const entry in props.schema.properties) {
      if (props.schema.properties[entry].default !== undefined) {
        model[entry] = props.schema.properties[entry].default;
      }
    }
  }
);

function onReset() {
  for (const key in model) {
    delete model[key];
  }
}
</script>
