/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { debounce } from 'quasar';

// As defined in the backend schema harbinger/schemas/search.py
export interface SearchResultItem {
  id: string;
  type: string;
  name: string;
  context: string | null;
  url: string;
}

export interface SearchState {
  searchQuery: string;
  searchResults: SearchResultItem[];
  isLoading: boolean;
  error: string | null;
}

export const useSearchStore = defineStore('search', {
  state: (): SearchState => ({
    searchQuery: '',
    searchResults: [],
    isLoading: false,
    error: null,
  }),
  actions: {
    // Debounce the search to prevent API calls on every keystroke
    debouncedSearch: debounce(async function (this: SearchState, query: string) {
      if (!query) {
        this.searchResults = [];
        this.isLoading = false;
        return;
      }

      this.isLoading = true;
      this.error = null;

      try {
        const response = await api.get<{ results: SearchResultItem[] }>('/search', {
          params: { q: query },
        });
        this.searchResults = response.data.results;
      } catch (e) {
        this.error = 'An error occurred while searching.';
        this.searchResults = [];
      } finally {
        this.isLoading = false;
      }
    }, 300), // 300ms debounce delay

    // This action is called by the component on input change
    async performSearch(query: string) {
      this.searchQuery = query;
      // The 'as any' is a workaround for 'this' context issues with debounced actions in Pinia
      (this as any).debouncedSearch(query);
    },
  },
});
