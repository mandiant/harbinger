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
      @keydown.down.prevent="handleArrowDown"
      @keydown.up.prevent="handleArrowUp"
      @keydown.enter.prevent="handleEnter"
      placeholder="Search or run command (Ctrl+K)..."
      class="q-ml-md"
      style="min-width: 400px"
      :loading="isLoading"
      ref="searchInputRef"
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
              :ref="(el) => setItemRef(item, el)"
              :class="{ 'selected-item': isSelected(item) }"
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

<style scoped>
.search-container {
  display: flex;
  justify-content: center;
  align-items: center;
}
.selected-item {
  background-color: #e0e0e0; /* A light grey for highlighting */
}
.body--dark .selected-item {
  background-color: #555; /* A darker grey for dark mode */
}
</style>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { useSearchStore, CombinedSearchResult } from 'src/stores/search';
import { storeToRefs } from 'pinia';
import { QInput } from 'quasar';

const router = useRouter();
const searchStore = useSearchStore();
const { searchQuery, isLoading, combinedResults } = storeToRefs(searchStore);
const { performSearch } = searchStore;

const searchInputRef = ref<QInput | null>(null);
const selectedIndex = ref(-1);
const itemRefs = ref<Record<string, any>>({});

const isMenuOpen = computed(() => {
  return searchQuery.value.length > 0;
});

// A flattened list of results for easy indexing with keyboard
const flatResults = computed(() => {
  return Object.values(groupedResults.value).flat();
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

// Reset selection when search query changes
watch(searchQuery, () => {
  selectedIndex.value = -1;
  itemRefs.value = {}; // Clear refs on new search
});

const setItemRef = (item: CombinedSearchResult, el: any) => {
  if (el) {
    // Use a unique key for each item
    const key = 'id' in item ? item.id : item.url;
    itemRefs.value[key] = el;
  }
};

const isSelected = (item: CombinedSearchResult) => {
  if (selectedIndex.value < 0) return false;
  const selectedItem = flatResults.value[selectedIndex.value];
  if (!selectedItem) return false;
  // Compare items based on a unique key
  const itemKey = 'id' in item ? item.id : item.url;
  const selectedKey = 'id' in selectedItem ? selectedItem.id : selectedItem.url;
  return itemKey === selectedKey;
};

const scrollToSelected = () => {
  if (selectedIndex.value < 0) return;
  const item = flatResults.value[selectedIndex.value];
  if (!item) return;
  const key = 'id' in item ? item.id : item.url;
  const el = itemRefs.value[key];
  if (el && el.$el) {
    el.$el.scrollIntoView({ block: 'nearest' });
  }
};

const handleArrowDown = () => {
  if (flatResults.value.length === 0) return;
  selectedIndex.value = (selectedIndex.value + 1) % flatResults.value.length;
  nextTick(scrollToSelected);
};

const handleArrowUp = () => {
  if (flatResults.value.length === 0) return;
  selectedIndex.value = (selectedIndex.value - 1 + flatResults.value.length) % flatResults.value.length;
  nextTick(scrollToSelected);
};

const handleEnter = () => {
  if (selectedIndex.value >= 0 && flatResults.value[selectedIndex.value]) {
    const item = flatResults.value[selectedIndex.value];
    navigate(item.url);
  }
};

const navigate = (url: string) => {
  router.push(url);
  // Clear search to hide menu after navigation
  performSearch('');
};

// Keyboard shortcut (Ctrl+K)
const handleKeyPress = (event: KeyboardEvent) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
    event.preventDefault();
    searchInputRef.value?.focus();
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleKeyPress);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyPress);
});
</script>