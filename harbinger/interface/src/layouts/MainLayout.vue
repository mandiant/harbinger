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
  <q-layout view="hHh Lpr lff" class="bg-image">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat @click="drawer = !drawer" round dense icon="menu" />
        <q-btn flat :to="'/'">
          <q-avatar>
            <img src="Harbinger.png" />
          </q-avatar>
        </q-btn>
        <q-toolbar-title>Harbinger</q-toolbar-title>

        <progress-bars />
        <event-web-socket />

        <q-btn-dropdown stretch flat :label="me.email">
          <q-list>
            <q-item @click="toggleDark" clickable v-show="!darkmode">
              <q-item-section avatar>
                <q-avatar color="secondary" text-color="white" icon="dark_mode" />
              </q-item-section>
              <q-item-section>Dark mode</q-item-section>
            </q-item>
            <q-item @click="toggleDark" clickable v-show="darkmode">
              <q-item-section avatar>
                <q-avatar color="secondary" text-color="white" icon="light_mode" />
              </q-item-section>
              <q-item-section>Light mode</q-item-section>
            </q-item>
            <q-item to="/settings" clickable>
              <q-item-section avatar>
                <q-avatar color="secondary" text-color="white" icon="settings" />
              </q-item-section>
              <q-item-section>Settings</q-item-section>
            </q-item>
            <q-item @click="openAdmin" clickable>
              <q-item-section avatar>
                <q-avatar color="secondary" text-color="white" icon="admin_panel_settings" />
              </q-item-section>
              <q-item-section>Admin panel</q-item-section>
            </q-item>
            <q-item clickable>
              <q-item-section avatar>
                <q-avatar color="secondary" text-color="white" icon="logout" />
              </q-item-section>
              <q-item-section @click="logOut">Logout</q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="drawer" bordered>
      <navigation-list />
    </q-drawer>

    <q-page-container>
      <bread-crumb />
      <router-view />
      <!-- <q-page-sticky position="bottom-right" :offset="[18, 72]">
        <q-fab icon="keyboard_arrow_up" label="Quick Access" direction="up" color="secondary">
          <q-fab-action color="primary" label="Upload files" icon="upload_file" to="/files/add_multiple" />
          <q-fab-action color="primary" label="Run playbook" icon="menu_book" to="/playbooks/add_from_template" />
        </q-fab>
      </q-page-sticky> -->
    </q-page-container>
  </q-layout>
</template>

<style scoped>
.bg-image {
  background-image: url(bg-right.png);
  background-repeat: no-repeat;
  background-size: contain;
  background-position: right;
  background-attachment: fixed;
}
</style>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';
import NavigationList from 'src/components/NavigationList.vue';
import EventWebSocket from 'src/components/EventWebSocket.vue';
import ProgressBars from 'src/components/ProgressBars.vue';
import BreadCrumb from 'src/components/BreadCrumb.vue';

const $q = useQuasar();
const $router = useRouter();

const darkmode = ref(false);

const drawer = ref(true);

const me = ref({ email: '' });

watch(darkmode, async (old, new_model) => {
  localStorage.dark = !new_model;
  $q.dark.set(!new_model);
});

function toggleDark() {
  darkmode.value = !darkmode.value;
  localStorage.dark = darkmode.value;
  $q.dark.set(darkmode.value);
}

function loadfromstorage() {
  if (localStorage.dark) {
    darkmode.value = localStorage.dark === 'true';
  }
}

loadfromstorage();

function openAdmin() {
  window.open('/admin/', '_blank');
}

function loadMe() {
  api
    .get('/users/me')
    .then((response) => {
      me.value = response.data;
    })
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    .catch(() => {});
}

loadMe();

function logOut() {
  api.post('/auth/logout').then(() => {
    $router.push({ name: 'login' });
  });
}

</script>
