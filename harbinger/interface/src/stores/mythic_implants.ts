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
import { C2Implant } from 'src/models';
import { api } from 'boot/axios';
import { debounce } from 'quasar';

export const useMythicImplantStore = defineStore('mythic_implant', {
  state: () => ({
    implants: new Map<string, C2Implant>(),
    aliveImplants: [] as C2Implant[],
  }),
  getters: {
    getImplant: (state) => {
      return (implant_id: string) => state.implants.get(implant_id)
    },
  },
  actions: {
    async loadImplant(implant_id: string) {
      return new Promise<C2Implant>((resolve, reject) => {
        if (!this.implants.has(implant_id)) {
          api
            .get(`/c2/implants/${implant_id}`)
            .then((response) => {
              this.implants.set(implant_id, response.data);
              resolve(response.data)
            }).catch(() => {
              reject()
            });
        } else {
          const impl = this.implants.get(implant_id)
          if(impl){
            resolve(impl)
          }
        }
      })
    },
    async LoadAliveImplants() {
      if(this.aliveImplants.length === 0){
        api
        .get('/c2/implants/', {params: {alive_only: true}})
        .then((response) => {
          this.aliveImplants = response.data.items;
          return this.aliveImplants
        });
      } else {
        return this.aliveImplants
      }
      return []
    },
    // Debounced version of ReLoadAliveImplants
    debouncedReLoadAliveImplants: debounce(async function (this: ReturnType<typeof useMythicImplantStore>) {
      api
        .get('/c2/implants/', { params: { alive_only: true } })
        .then((response) => {
          this.aliveImplants = response.data.items;
        });
    }, 1000, true), // Adjust the debounce delay (in milliseconds) as needed
    ReLoadAliveImplants() {
      this.debouncedReLoadAliveImplants();
    },
  }
});
