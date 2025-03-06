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
    <bread-crumb />
    <q-tabs v-model="tab" dense class="text-grey" active-color="primary" indicator-color="primary" align="justify"
      narrow-indicator>
      <q-tab icon="settings" name="harbinger" label="Harbinger Settings"
        :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
      <q-tab icon="manage_accounts" name="user" label="User settings" :class="$q.dark.isActive ? 'text-white' : 'text-black'" />
    </q-tabs>
    <q-separator />
    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="harbinger"><harbinger-settings /></q-tab-panel>
      <q-tab-panel name="user"><user-settings /></q-tab-panel>
    </q-tab-panels>

  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import BreadCrumb from '../components/BreadCrumb.vue';
import HarbingerSettings from 'src/components/HarbingerSettings.vue';
import UserSettings from 'src/components/UserSettings.vue';

const tab = ref('harbinger')

</script>
