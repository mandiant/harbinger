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
import { Label, LabelView } from 'src/models';
import { api } from 'boot/axios';


export const useLabelStore = defineStore('labels_old', {
  state: () => ({
    labels: Array<Label>(),
    label_category_map: new Map<string, Array<Label>>()
  }),

  getters: {
    getLabels(state) {
      return state.labels
    }
  },
  actions: {
    getLabel(id: string) {
      const res = this.labels.filter((element:Label) => element.id === id);
      if (res) {
        return res[0];
      }
      return {} as Label
    },
    loadLabels() {
      api
        .get('/labels/grouped')
        .then((response) => {
          this.labels = []
          this.label_category_map = new Map<string, Array<Label>>()
          response.data.forEach((element: LabelView) => {
            element.labels.forEach((element: Label) => {
              this.labels.push(element);
            })
            this.label_category_map.set(element.category, element.labels);
          });
        })
        // eslint-disable-next-line @typescript-eslint/no-empty-function
        .catch(() => {});
    },
  }
});
