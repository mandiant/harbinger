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

import { ref } from 'vue';
import { api } from 'boot/axios';
import { Pagination } from './models';
export default function <Type>(endpoint: string) {
  const loading = ref(false);
  const data = ref<Type>([] as Type);

  const filters = ref({});

  const url = `/${endpoint}/`;

  const pagination = ref<Pagination>({
    sortBy: '',
    descending: false,
    page: 1,
    rowsPerPage: 15,
    rowsNumber: 1,
  });

  function onRequest(props: {
    pagination: {
      sortBy: string;
      descending: boolean;
      page: number;
      rowsPerPage: number;
    };
    filter?: object;
    getCellValue: object;
  }) {
    pagination.value.page = props.pagination.page;
    pagination.value.rowsPerPage = props.pagination.rowsPerPage;
    pagination.value.sortBy = props.pagination.sortBy;
    pagination.value.descending = props.pagination.descending;
    loadData();
  }

  function AddFilter(filter: object) {
    filters.value = { ...filters.value, ...filter };
  }

  interface PaginationForm {
    page: number;
    size: number;
    order_by?: string;
  }

  function loadData() {
    loading.value = true;
    const stuff: PaginationForm = {
      page: pagination.value.page,
      size: pagination.value.rowsPerPage,
    }

    if(pagination.value.sortBy){
      stuff.order_by = pagination.value.descending ? `-${pagination.value.sortBy}` : pagination.value.sortBy
    }

    const nonEmptyFilters = {}
    for (const [key, value] of Object.entries(filters.value)) {
      if (value) {
        nonEmptyFilters[key] = value;
      }
    }
    api
      .get(url, { params: { ...nonEmptyFilters, ...stuff } })
      .then((response) => {
        data.value = response.data.items;
        pagination.value.page = response.data.page;
        pagination.value.rowsNumber = response.data.total;
        loading.value = false;
      })
      .catch(() => {
        loading.value = false;
      });
  }
  return {
    loading,
    data,
    pagination,
    loadData,
    onRequest,
    AddFilter,
  };
}
