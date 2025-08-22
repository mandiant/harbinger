<!--
 Copyright 2025 Google LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
-->

<template>
  <q-page padding>
    
    <q-btn color="secondary" icon="refresh" @click="loadData()">Refresh</q-btn>
    <q-table :rows-per-page-options="[ 5, 10, 15, 20, 25, 50, 100 ]" title="Components" :rows="data" row-key="id" :loading="loading">
    </q-table>
  </q-page>
</template>

<script setup lang="ts">

import useloadData from 'src/load-data';
import { Component } from '../models';
const { loading, data, loadData } =
  useloadData<Array<Component>>('components');
loadData();
</script>
