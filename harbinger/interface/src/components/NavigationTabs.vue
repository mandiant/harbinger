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
  <q-tabs inline-label vertical>
    <q-route-tab label="Dashboard" icon="dashboard" to="/" exact />
    <q-route-tab label="Socks Jobs" icon="work" to="/proxy_jobs" exact />
    <q-route-tab
      label="Credentials"
      icon="fingerprint"
      to="/credentials"
      exact
    />
    <q-route-tab label="Proxies" icon="share" to="/proxies" exact />
    <q-route-tab label="Files" icon="article" to="/files" exact />
    <q-route-tab label="Domains" icon="corporate_fare" to="/domains" exact />
    <q-route-tab label="Passwords" icon="key" to="/passwords" exact />
    <q-route-tab label="Computers" icon="computer" to="/computers" exact />
    <q-route-tab label="Users" icon="person" to="/users" exact />
    <q-route-tab label="Groups" icon="group" to="/groups" exact />
    <q-route-tab label="Playbook" icon="link" to="/playbooks" exact />
    <q-route-tab
      label="C2 jobs"
      to="/c2_jobs"
      exact
      icon="fas fa-satellite-dish"
    />
    <q-route-tab
      label="BloodHound Utils"
      to="/bloodhound_utils"
      exact
      icon="img:bloodhound.png"
    />
    <q-route-tab
      label="Suggested actions"
      to="/suggestions"
      exact
      icon="fas fa-robot"
    />
  </q-tabs>
</template>

<script setup lang="ts"></script>
