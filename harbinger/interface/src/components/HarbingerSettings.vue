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
  <div>Harbinger settings
    <q-list bordered>
      <q-expansion-item expand-separator :label="entry.name" v-for="entry, index in settings" v-bind:key="index"
        default-opened :icon="entry.icon" :caption="entry.description" class="q-gutter-md">
        <q-form @submit="onSubmit(entry)">
          <q-item v-for="setting in entry.settings" v-bind:key="setting.id">
            <q-item-section>
              <q-input v-model="setting.value" v-if="setting.type === 'str'" :label="setting.name"
                :hint="setting.description" autogrow/>
              <q-select :label="setting.name" :hint="setting.description" v-model="setting.value"
                v-if="setting.type === 'list'" use-chips hide-dropdown-icon new-value-mode="add-unique" multiple
                use-input />
              <q-input :label="setting.name" :hint="setting.description" v-model.number="setting.value" type="number"
                v-if="setting.type === 'int'" />
            </q-item-section>
          </q-item>
          <q-item>
            <q-btn label="Save" type="submit" color="secondary" :loading="loading" />
          </q-item>
        </q-form>
        <q-inner-loading :showing="loading">
          <q-spinner-gears size="50px" color="secondary" />
        </q-inner-loading>
      </q-expansion-item>
    </q-list>
  </div>
</template>

<script setup lang="ts">
import { api } from 'boot/axios';
import { ref } from 'vue';
import { Settings } from 'src/models';
import { useQuasar } from 'quasar';

const $q = useQuasar();

const settings = ref<Array<Settings>>([]);
const loading = ref(false);

function LoadData() {
  loading.value = true;
  api.get('/settings/').then((response) => {
    settings.value = response.data;
    loading.value = false;
  })
}
LoadData();

function onSubmit(setting: Settings) {
  loading.value = true;
  var requests: Array<Promise<unknown>> = [];
  setting.settings.forEach((element) => {
    requests.push(api.patch(`/settings/${element.id}`, { value: element.value }))
  })

  Promise.all(requests).then(() => {
    loading.value = false;
    $q.notify({
      color: 'positive',
      position: 'top',
      message: 'Saved settings',
      icon: 'report_problem',
    });
    LoadData();
  })
}

</script>
