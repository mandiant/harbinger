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
import { Pagination, KeyValue } from '../models';
import { toRaw } from 'vue';

interface PaginationForm {
  page: number;
  size: number;
  order_by?: string;
}

export const defineTypedStore = <T>(id: string) => defineStore(id, {
  state: () => ({
    data_loaded: false,
    data: Array<T>(),
    filters: {} as KeyValue,
    loading: false,
    url: `/${id}/`,
    pagination: {
      sortBy: '',
      descending: false,
      page: 1,
      rowsPerPage: 15,
      rowsNumber: 1,
    } as Pagination,
    cache: {} as { [key: string]: T },
  }),
  getters: {
    getData(state) {
      return state.data
    },
  },
  actions: {
    // Checks if the data has not been loaded yet, use this function in component startup.
    Load() {
      if (!this.data_loaded || this.data.length === 0) {
        this.LoadData()
      }
    },
    // Force reload the data.
    LoadData() {
      this.loading = true;
      const form: PaginationForm = {
        page: this.pagination.page,
        size: this.pagination.rowsPerPage,
      }
      if (this.pagination.sortBy) {
        form.order_by = this.pagination.descending ? `-${this.pagination.sortBy}` : this.pagination.sortBy
      }
      const nonEmptyFilters: KeyValue = {}
      for (const [key, value] of Object.entries(this.filters)) {
        if (value) {
          nonEmptyFilters[key] = value;
        }
      }
      api
        .get(this.url, { params: { ...nonEmptyFilters, ...form } })
        .then((response) => {
          this.data = response.data.items;
          this.pagination.page = response.data.page;
          this.pagination.rowsNumber = response.data.total;
          this.data_loaded = true;
          this.loading = false;
        })
        .catch(() => {
          this.loading = false;
        });
    },
    onRequest(props: {
      pagination: {
        sortBy: string;
        descending: boolean;
        page: number;
        rowsPerPage: number;
      };
      filter?: object;
      getCellValue: object;
    }) {
      this.pagination.page = props.pagination.page;
      this.pagination.rowsPerPage = props.pagination.rowsPerPage;
      this.pagination.sortBy = props.pagination.sortBy;
      this.pagination.descending = props.pagination.descending;
      this.LoadData();
    },
    AddFilter(filter: object) {
      this.filters = { ...this.filters, ...filter };
    },
    RemoveFilter(key: string) {
      if (key in this.filters) {
        const newFilters = { ...this.filters };
        delete newFilters[key];
        this.filters = newFilters;
        this.LoadData();
      }
    },
    updateFilters() {
      this.AddFilter(toRaw(this.filters));
      this.LoadData();
    },
    updateCache(id: string) {
      this.Load();
      api
        .get(`${this.url}${id}`, {})
        .then((response) => {
          this.cache[id] = response.data
          try {
            const index = this.data.findIndex(item => item.id === id);
            if (index !== -1) {
              this.data[index] = response.data;
            } else {
              // Entry not found, possibly a new entry. Reload the data if the page is 1.
              if (this.pagination.page === 1) {
                this.LoadData();
              }
            }
          } catch {
            this.LoadData();
          }
        })
        // eslint-disable-next-line @typescript-eslint/no-empty-function
        .catch(() => { });
    },
    loadById(id: string): Promise<T | null> {
      return new Promise(async (resolve, reject) => {
        if (this.cache[id]) {
          resolve(this.cache[id]);
          return
        }
        api
          .get(`${this.url}${id}`, {})
          .then((response) => {
            this.cache[id] = response.data
            resolve(response.data);
          })
          .catch(() => {
            reject();
          });
      });
    }
  }
});
