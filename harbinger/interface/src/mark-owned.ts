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

import { api } from 'boot/axios';
import { useQuasar } from 'quasar';
export default function () {
  const $q = useQuasar();

  function markOwned(name: string, fn?: () => void) {
    api
      .post('/graph/mark_owned', { names: [name] })
      .then((response) => {
        if (response.data.count === 1) {
          $q.notify({
            color: 'positive',
            position: 'top',
            message: `${response.data.count} Object marked!`,
            icon: 'report_problem',
          });
        } else if (response.data.count > 0) {
          $q.notify({
            color: 'positive',
            position: 'top',
            message: `${response.data.count} Objects marked!`,
            icon: 'report_problem',
          });
        } else {
          $q.notify({
            color: 'warning',
            position: 'top',
            message: 'No object marked!',
            icon: 'report_problem',
          });
        }
        if (fn) {
          fn();
        }
      })
      .catch(() => {
        $q.notify({
          color: 'negative',
          position: 'top',
          message: 'Unable to mark as owned.',
          icon: 'report_problem',
        });
      });
  }

  function unmarkOwned(name: string, fn?: () => void) {
    api
      .post('/graph/unmark_owned', { names: [name] })
      .then((response) => {
        if (response.data.count === 1) {
          $q.notify({
            color: 'positive',
            position: 'top',
            message: `${response.data.count} Object marked!`,
            icon: 'report_problem',
          });
        } else if (response.data.count > 0) {
          $q.notify({
            color: 'positive',
            position: 'top',
            message: `${response.data.count} Objects marked!`,
            icon: 'report_problem',
          });
        } else {
          $q.notify({
            color: 'warning',
            position: 'top',
            message: 'No object marked!',
            icon: 'report_problem',
          });
        }
        if (fn) {
          fn();
        }
      })
      .catch(() => {
        $q.notify({
          color: 'negative',
          position: 'top',
          message: 'Unable to unmark as owned.',
          icon: 'report_problem',
        });
      });
  }
  return {
    markOwned,
    unmarkOwned,
  };
}
