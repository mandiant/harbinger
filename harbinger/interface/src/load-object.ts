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
import { useQuasar } from 'quasar';
export default function <Type>(endpoint: string, id: number | string) {
  const $q = useQuasar();
  const loading = ref(false);
  const object = ref<Type>({} as Type);

  function loadObject() {
    loading.value = true;
    api
      .get(`/${endpoint}/${id}`)
      .then((response) => {
        object.value = response.data;
        loading.value = false;
      })
      .catch((error) => {
        loading.value = false;
        $q.notify({
          color: 'negative',
          position: 'top',
          message: `Loading failed: ${error.message}`,
          icon: 'report_problem',
        });
      });
  }
  return {
    loading,
    object,
    loadObject,
  };
}
