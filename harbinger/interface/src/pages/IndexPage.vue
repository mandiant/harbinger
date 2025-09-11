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
    <div class="row q-gutter-md justify-center">
      <statistics-view v-for="(statistic, index) in statistics" v-bind:key="index" :url="statistic.url"
        :icon="statistic.icon" :name="statistic.name" :to="statistic.to" />
    </div>
  </q-page>
</template>

<script setup lang="ts">
import StatisticsView from 'src/components/StatisticsView.vue';
import { StatisticViewModel } from 'src/models';

const statistics: Array<StatisticViewModel> = [
  {
    url: 'statistics/job',
    icon: 'work',
    name: 'Job Overview',
    to: [{ to: '/proxy_jobs', label: 'Socks Jobs' }, { to: '/c2_jobs', label: 'C2 Jobs' }]
  },
  {
    url: 'graph/stats',
    icon: 'img:bloodhound.png',
    name: 'Bloodhound Statistics',
    to: [{ to: '/bloodhound_utils', label: 'BloodHound utils' }]
  },
  {
    url: 'graph/owned_stats',
    icon: 'img:bloodhound.png',
    name: 'Admin Statistics',
    to: [{ to: '/bloodhound_utils', label: 'BloodHound utils' }]
  },
  {
    url: 'statistics/implant',
    icon: 'fas fa-satellite-dish',
    name: 'Implants',
    to: [{ to: '/implants', label: 'Implants' }]
  },
  // {
  //   url: 'situational_awareness_statistics',
  //   icon: 'travel_explore',
  //   name: 'Situational Awareness Overview',
  //   to: [{ to: '/situational_awareness', label: 'Situational Awareness' }]
  // },
  {
    url: 'statistics/share',
    icon: 'folder_shared',
    name: 'Share Overview',
    to: [{ to: '/shares', label: 'Shares' }]
  },
  {
    url: 'statistics/server',
    icon: 'dns',
    name: 'Server Overview',
    to: [{ to: '/servers', label: 'C2 Servers' }, { to: '/socks_servers', label: 'Socks Servers'}]
  }
]

</script>
