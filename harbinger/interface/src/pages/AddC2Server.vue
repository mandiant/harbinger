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
  <q-page padding>
    
    <q-card flat class="q-pa-md">
      <q-card-section>
        <h5>Add a c2 server</h5>
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <q-select filled :options="data" option-label="name" v-model="tab" label="type" />
          <template v-if="tab && tab.arguments">
            <div class="text-h6">{{ tab.name }}</div>
            <q-input filled v-model="form.name" label="name" lazy-rules />
            <template v-for="argument in tab.arguments" v-bind:key="argument.name">
              <q-input :type="argument.type" filled v-model="form[argument.name]" :label="argument.name"
                :error="!form[argument.name]" lazy-rules
                :rules="[val => checkValue(argument.regex || '', val) || argument.error]" />
            </template>
          </template>
          <div v-if="tab">
            <q-btn label="Submit" type="submit" color="secondary" :loading="loading" />
            <q-btn label="Reset" type="reset" color="seconday" flat class="q-ml-sm" />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref, watch } from 'vue';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';

import useloadData from 'src/load-data';
import { C2ServerType } from 'src/models'

const $q = useQuasar();
const $router = useRouter();

const { loading, data, loadData } =
  useloadData<Array<C2ServerType>>('c2_server_types');

loadData()
const tab = ref(null as C2ServerType | null);

interface Form {
  type: string;
  name: string;
  hostname?: string | null;
  username?: string | null;
  port: number | null;
  password?: string | null;
  ca_certificate?: string | null;
  certificate?: string | null;
  private_key?: string | null;
  token?: string | null;
}

const form = ref({} as Form)

function onSubmit() {
  form.value.type = tab.value.name
  if (form.value.name != null) {
    loading.value = true;
    api
      .post('/c2_servers/', form.value)
      .then((response) => {
        $q.notify({
          color: 'green-4',
          textColor: 'white',
          icon: 'cloud_done',
          position: 'top',
          message: `Submitted, c2 id: ${response.data.id}`,
        });
        $router.push({ name: 'servers' });
        loading.value = false;
      })
      .catch(() => {
        loading.value = false;
        $q.notify({
          color: 'negative',
          position: 'top',
          message: 'Loading failed',
          icon: 'report_problem',
        });
      });
  } else {
    $q.notify({
      color: 'red-5',
      textColor: 'white',
      icon: 'warning',
      position: 'top',
      message: 'You need to fill in everything',
    });
  }
}

function onReset() {
  form.value = {} as Form
}

function checkValue(regex: string, value: string | undefined) {
  if (regex !== '' && value){
    const re = new RegExp(regex)
    return re.test(value)
  } else {
    return value !== '' && value !== undefined
  }
}

watch(tab, (old, new_model) => {
  if (old !== new_model && tab.value) {
    form.value.name = `${tab.value.name}1`
    tab.value.arguments.forEach(element => {
      if(element.default){
        form.value[element.name] = element.default
      }
    })
  }
});
</script>
