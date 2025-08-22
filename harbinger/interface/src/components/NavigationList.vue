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
  <q-list bordered>
    <q-item clickable v-ripple to="/" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="dashboard" color="secondary" />
      </q-item-section>
      <q-item-section>Dashboard</q-item-section>
    </q-item>
    <q-separator />

    <div v-for="group in menuGroups" :key="group.name">
      <q-item-label header class="text-weight-bold text-uppercase">
        {{ group.name }}
      </q-item-label>
      <menu-item v-for="item in group.items" :key="item.name" :item="item" />
      <q-separator />
    </div>
  </q-list>
</template>

<script setup lang="ts">
import { useNavigationStore } from 'src/stores/navigation';
import { storeToRefs } from 'pinia';
import MenuItem from './MenuItem.vue';

const navigationStore = useNavigationStore();
const { menuGroups } = storeToRefs(navigationStore);
</script>
