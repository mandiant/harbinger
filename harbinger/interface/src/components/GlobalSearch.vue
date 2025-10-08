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
  <div class="search-container">
    <q-input
      dark
      dense
      standout
      :model-value="searchQuery"
      @update:model-value="performSearch"
      placeholder="Search or run command (Ctrl+K)..."
      class="q-ml-md"
      style="min-width: 400px"
      :loading="isLoading"
    >
      <template v-slot:prepend>
        <q-icon name="search" />
      </template>
      <q-menu
        v-model="isMenuOpen"
        no-focus
        no-parent-event
        fit
        anchor="bottom left"
        self="top left"
      >
        <q-list bordered separator style="max-height: 400px; overflow-y: auto">
          <div v-if="isLoading && combinedResults.length === 0" class="q-pa-md">
            <q-item-label class="text-center">
              <q-spinner color="primary" size="2em" />
            </q-item-label>
          </div>
          <div
            v-else-if="!isLoading && combinedResults.length === 0 && searchQuery"
            class="q-pa-md"
          >
            <q-item-label class="text-center">No results found.</q-item-label>
          </div>
          <template v-for="(group, type) in groupedResults" :key="type">
            <q-item-label header class="bg-grey-2 text-primary">{{
              type
            }}</q-item-label>
            <q-item
              v-for="item in group"
              :key="item.url"
              clickable
              v-ripple
              @click="navigate(item.url)"
            >
              <q-item-section avatar v-if="item.type === 'Command'">
                <q-icon name="keyboard_arrow_right" />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ item.name }}</q-item-label>
                <q-item-label caption v-if="item.context">{{
                  item.context
                }}</q-item-label>
              </q-item-section>
            </q-item>
          </template>
        </q-list>
      </q-menu>
    </q-input>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSearchStore, CombinedSearchResult } from 'src/stores/search';
import { storeToRefs } from 'pinia';

const router = useRouter();
const searchStore = useSearchStore();
const { searchQuery, isLoading, combinedResults } = storeToRefs(searchStore);
const { performSearch } = searchStore;

const isMenuOpen = computed(() => {
  return searchQuery.value.length > 0;
});

const groupedResults = computed(() => {
  return combinedResults.value.reduce((acc, item) => {
    const type = item.type === 'Command' ? 'Commands' : item.type;
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(item);
    return acc;
  }, {} as Record<string, CombinedSearchResult[]>);
});

const navigate = (url: string) => {
  router.push(url);
  // Clear search to hide menu after navigation
  performSearch('');
};

// Keyboard shortcut (Ctrl+K)
const handleKeyPress = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
    event.preventDefault();
    const searchInput = document.querySelector('.search-container input') as HTMLInputElement;
    if (searchInput) {
      searchInput.focus();
    }
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleKeyPress);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyPress);
});
</script>
