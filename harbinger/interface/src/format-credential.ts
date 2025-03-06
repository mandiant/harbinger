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

import { Credential, Password } from './models';

export function formatCredential(obj: Credential) {
  if (obj === null) {
    return '';
  }

  let result = '';

  if (obj.domain) {
    result += obj.domain.long_name;
    result += '\\';
  }

  result += obj.username + ':' + formatPassword(obj.password);

  return result;
}

export function formatPassword(obj: Password) {
  if (obj === null) {
    return 'null';
  }
  if (obj.password !== null) {
    return obj.password;
  }
  if (obj.nt !== null) {
    return obj.nt;
  }
  if (obj.aes128_key !== null) {
    return obj.aes128_key;
  }
  if (obj.aes256_key !== null) {
    return obj.aes256_key;
  }
}
