// src/stores/datastore.ts

import { defineStore, Store } from 'pinia';
import { api } from 'boot/axios';
import { Pagination, KeyValue } from '../models';
import { toRaw } from 'vue';

interface BaseModel {
  id: string | number;
  [key: string]: any;
}

interface PaginationForm {
  page: number;
  size: number;
  order_by?: string;
}

// Define an interface for the specific actions we've added to our typed stores
export interface CrudActions<T extends BaseModel> {
  addObject(obj: T): void;
  updateObject(obj: T): void;
  deleteObject(id: T['id']): void;
}

// Combine Pinia's Store type with our custom actions
// This tells TypeScript that the returned store will have these CRUD methods.
export type TypedStore<T extends BaseModel> = Store<string, any, any, CrudActions<T>>;


export const defineTypedStore = <T extends BaseModel>(id: string) => {
  const storeId = `datastore/${id.replace(/\//g, '_')}`; // Ensure store ID is unique and valid

  const storeDefinition = defineStore(storeId, {
    state: () => ({
      data_loaded: false,
      data: [] as T[],
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
      cache: new Map<T['id'], T>(),
    }),
    getters: {
      getData(state) {
        return state.data
      },
      getItemFromCache: (state) => (id: T['id']): T | undefined => {
        return state.cache.get(id);
      },
      isItemInCurrentView: (state) => (id: T['id']): boolean => {
        return state.data.some(item => item.id === id);
      },
    },
    actions: {
      Load() {
        if (!this.data_loaded || this.data.length === 0 || this.cache.size === 0) {
          this.LoadData();
        }
      },
      async LoadData() {
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
        try {
          const response = await api.get(this.url, { params: { ...nonEmptyFilters, ...form } });
          this.data = response.data.items;
          this.pagination.page = response.data.page;
          this.pagination.rowsNumber = response.data.total;
          this.data_loaded = true;

          this.cache.clear();
          response.data.items.forEach((item: T) => {
            this.cache.set(item.id, item);
          });

        } catch (error) {
          console.error(`Failed to load data for ${id} store:`, error);
        } finally {
          this.loading = false;
        }
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

      addObject(obj: T) {
        if (!obj || obj.id === undefined) {
          console.warn(`Attempted to add object without a valid ID to ${id} store:`, obj);
          return;
        }

        this.cache.set(obj.id, obj);

        const isVisibleInCurrentPage = this.data.length < this.pagination.rowsPerPage && this.pagination.page === 1;
        const matchesFilters = true; // Placeholder: Implement actual filter matching if needed

        if (isVisibleInCurrentPage && matchesFilters) {
          this.data.unshift(obj);
          if (this.data.length > this.pagination.rowsPerPage) {
            this.data.pop();
          }
          this.pagination.rowsNumber++;
        } else if (matchesFilters && this.pagination.page === 1) {
            this.pagination.rowsNumber++;
        } else {
          this.pagination.rowsNumber++;
        }
      },

      updateObject(obj: T) {
        if (!obj || obj.id === undefined) {
          console.warn(`Attempted to update object without a valid ID in ${id} store:`, obj);
          return;
        }

        const existingInCache = this.cache.get(obj.id);
        if (existingInCache) {
          this.cache.set(obj.id, { ...existingInCache, ...obj });
        } else {
          this.cache.set(obj.id, obj);
          console.warn(`[${id}] Object ${obj.id} not found in cache during update, adding it.`);
        }

        const indexInView = this.data.findIndex(item => item.id === obj.id);
        if (indexInView !== -1) {
          this.data[indexInView] = { ...this.data[indexInView], ...obj };
        }
      },

      deleteObject(idToDelete: T['id']) {
        if (idToDelete === undefined) {
          console.warn(`Attempted to delete object without a valid ID from ${id} store.`);
          return;
        }

        if (this.cache.has(idToDelete)) {
          this.cache.delete(idToDelete);
        } else {
          console.warn(`[${id}] Attempted to delete non-existent object ${idToDelete} from cache.`);
        }

        const indexInView = this.data.findIndex(item => item.id === idToDelete);
        if (indexInView !== -1) {
          this.data.splice(indexInView, 1);
          this.pagination.rowsNumber--;

          if (this.data.length < this.pagination.rowsPerPage && this.pagination.rowsNumber > this.data.length) {
            this.LoadData();
          }
        } else if (this.pagination.rowsNumber > 0) {
          this.pagination.rowsNumber--;
        }
      },

      async updateCache(id: T['id']): Promise<T | undefined> {
        try {
          const response = await api.get(`${this.url}${id}`, {});
          const data: T = response.data;
          this.updateObject(data)
          return data;
        } catch (error) {
          console.error(`[${id}] Failed to fetch and cache item ID ${id}:`, error);
          throw error; // Re-throw to propagate the error
        }
      },
      async getOrFetch(id: T['id']): Promise<T | undefined> {
        if (this.cache.has(id)) {
          return this.cache.get(id);
        }
        return this.updateCache(id);
      },
      async loadById(id: T['id'], force = false): Promise<T | undefined> {
        if (force) {
          return this.updateCache(id);
        } else {
          return this.getOrFetch(id);
        }
      }
    }
  });

  // Explicitly cast the return type of defineStore
  return storeDefinition as unknown as TypedStore<T>;
};
