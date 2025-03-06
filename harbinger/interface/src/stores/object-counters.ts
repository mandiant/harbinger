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


interface Map {
  [key: string]: number
}

export const useCounterStore = defineStore('counter', {
  state: () => ({
    connected: false,
    data: {} as Map,
  }),
  getters: {
    isConnected: (state) => state.connected,
  },
  actions: {
    incrementObject(object_type: string) {
      if (!(object_type in this.data)) {
        this.data[object_type] = 0;
      }
      this.data[object_type] = this.data[object_type] + 1
    },
    setConnected() {
      this.connected = true;
    },
    setDisconnected() {
      this.connected = false;
    },
    get(key: string) {
      if (key in this.data) {
        return this.data[key];
      }
      return 0;
    },
    clear(key: string) {
      return this.data[key] = 0;
    }
  },
});
