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
import { Progress } from '../models';


export const useProgressStore = defineStore('progress', {
  state: () => ({
    progress: Array<Progress>(),
  }),
  getters: {
    getProgress(state) {
      return state.progress
    }
  },
  actions: {
    AddProgress(progress: Progress) {
      this.progress.push(progress)
    },
    UpdateProgress(id: string, current: number, percentage: number) {
      this.progress.forEach((element: Progress) => {
        if(element.id === id){
          element.percentage = percentage
          element.current = current
        }
      });
    },
    DeleteProgress(id: string) {
      setTimeout(() => {
        this.progress = this.progress.filter((e: Progress)=> e.id !== id)
      }, 2000)
    },
    loadProgressBars() {
      api
      .get('/progress_bars/')
      .then((response) => {
        this.progress = response.data;
      })
      // eslint-disable-next-line @typescript-eslint/no-empty-function
      .catch(() => {});
    },
  }
});
