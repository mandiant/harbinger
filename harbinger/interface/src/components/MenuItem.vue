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
  <!-- Regular Menu Item -->
  <q-item
    v-if="!item.children.length"
    clickable
    v-ripple
    :to="item.path"
    exact
    :class="$q.dark.isActive ? 'text-white' : 'text-black'"
  >
    <q-item-section avatar>
      <q-icon :name="item.icon" color="secondary" />
    </q-item-section>
    <q-item-section>{{ item.displayName }}</q-item-section>
    <q-item-section side v-if="count > 0">
      <q-badge color="secondary" :label="count" />
    </q-item-section>
  </q-item>

  <!-- Collapsible Parent Menu Item -->
  <q-expansion-item
    v-else
    :icon="item.icon"
    :label="item.displayName"
    :header-class="$q.dark.isActive ? 'text-white' : 'text-black'"
    expand-icon-class="text-secondary"
  >
    <template v-slot:header>
      <q-item-section avatar>
        <q-icon :name="item.icon" color="secondary" />
      </q-item-section>
      <q-item-section>
        {{ item.displayName }}
      </q-item-section>
      <q-item-section side v-if="count > 0">
        <q-badge color="secondary" :label="count" />
      </q-item-section>
    </template>

    <!-- Nested Children -->
    <q-list class="q-pl-lg">
      <menu-item v-for="child in item.children" :key="child.name" :item="child" />
    </q-list>
  </q-expansion-item>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { MenuItem } from 'src/stores/navigation';
import { useCounterStore } from 'src/stores/object-counters';
import { storeToRefs } from 'pinia';

const props = defineProps<{
  item: MenuItem;
}>();

const counterStore = useCounterStore();
const { data } = storeToRefs(counterStore);

const count = computed(() => {
  const itemName = props.item.name;
  if (itemName === 'credentials') {
    return (data.value['credential'] || 0) + (data.value['password'] || 0) + (data.value['kerberos'] || 0) + (data.value['hash'] || 0);
  }
  if (itemName === 'certificates') {
    return (data.value['certificate_template'] || 0) + (data.value['certificate_authority'] || 0);
  }
  return data.value[itemName] || 0;
});
</script>
