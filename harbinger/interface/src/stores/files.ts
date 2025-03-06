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
import { File } from 'src/models';
import { api } from 'boot/axios';


interface FileDict {
  [id: string]: File;
}

export const useFileStore = defineStore('old_files', {
  state: () => ({
    files: Array<File>(),
    filesDict: {} as FileDict,
    fileTypes: Array<string>(),
  }),
  getters: {
    getFiles(state) {
      return state.files
    },
    getFileTypes(state) {
      return state.fileTypes
    }
  },
  actions: {
    loadFileTypes() {
      api
      .get('/file_types/')
      .then((response) => {
        this.fileTypes = response.data.types;
      })
      // eslint-disable-next-line @typescript-eslint/no-empty-function
      .catch(() => {});
    },
    loadFiles() {
      api
        .get('/files/', {
          params: {
            page: 1,
            size: 100,
          }
        })
        .then((response) => {
          this.files = response.data.items
          this.files.forEach(element => {
            this.filesDict[element.id] = element
          })
        })
        // eslint-disable-next-line @typescript-eslint/no-empty-function
        .catch(() => {});
    },
    async getFile(id: string) {
      return new Promise<File>((resolve, reject) => {
        let file = this.filesDict[id]
        if (!file){
          api
          .get(`/files/${id}`, {})
          .then((response) => {
            file = response.data
            this.filesDict[id] = file
            resolve(file)
          })
          .catch(() => {
            reject()
          });
        }
        resolve(file)
      })
    }
  }
});
