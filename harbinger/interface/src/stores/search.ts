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

export interface StaticCommand {
  name: string;
  url: string;
  type: 'Command';
  context: string;
}

export type CombinedSearchResult = SearchResultItem | StaticCommand;

export interface SearchState {
  searchQuery: string;
  searchResults: SearchResultItem[];
  isLoading: boolean;
  error: string | null;
  staticCommands: StaticCommand[];
}

export const useSearchStore = defineStore('search', {
  state: (): SearchState => ({
    searchQuery: '',
    searchResults: [],
    isLoading: false,
    error: null,
    staticCommands: [
      { name: 'Add Credential', url: '/credentials/add', type: 'Command', context: 'Add a new credential.' },
      { name: 'Upload File', url: '/files/add', type: 'Command', context: 'Upload a single file.' },
      { name: 'Upload Multiple Files', url: '/files/add_multiple', type: 'Command', context: 'Upload multiple files at once.' },
      { name: 'Add Playbook', url: '/playbooks/add', type: 'Command', context: 'Create a new playbook.' },
      { name: 'Run Playbook from Template', url: '/playbooks/add_from_template', type: 'Command', context: 'Start a new playbook from a template.' },
      { name: 'Create Playbook Template', url: '/playbooks/add_template', type: 'Command', context: 'Create a new playbook template.' },
      { name: 'Create Playbook with AI', url: '/playbooks/add_template_ai', type: 'Command', context: 'Use AI to generate a new playbook.' },
      { name: 'Add C2 Server', url: '/servers/add', type: 'Command', context: 'Add a new C2 server.' },
      { name: 'Run C2 Job from Template', url: '/c2_jobs/add_from_template', type: 'Command', context: 'Run a C2 job from a template.' },
      { name: 'Add Socks Job', url: '/proxy_jobs/add', type: 'Command', context: 'Create a new socks proxy job.' },
      { name: 'Add Issue', url: '/issues/add', type: 'Command', context: 'Create a new issue.' },
      { name: 'Add Plan', url: '/plans/add', type: 'Command', context: 'Create a new AI plan.' },
      { name: 'Add Domain', url: '/domains/add', type: 'Command', context: 'Add a new domain.' },
      { name: 'Add Password', url: '/passwords/add', type: 'Command', context: 'Add a new password.' },
      { name: 'Add Label', url: '/labels/add', type: 'Command', context: 'Create a new label.' },
      { name: 'Create Timeline', url: '/timeline/create', type: 'Command', context: 'Generate a new timeline report.' },
      { name: 'Add Objective', url: '/objectives/add', type: 'Command', context: 'Add a new objective.' },
    ],
  }),
  getters: {
    combinedResults(state): CombinedSearchResult[] {
      const filteredCommands = state.searchQuery
        ? state.staticCommands.filter((command) =>
            command.name.toLowerCase().includes(state.searchQuery.toLowerCase())
          )
        : [];
      return [...filteredCommands, ...state.searchResults];
    },
  },
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
    performSearch(query: string) {
      this.searchQuery = query;
      // The 'as any' is a workaround for 'this' context issues with debounced actions in Pinia
      (this as any).debouncedSearch(query);
    },
  },
});
