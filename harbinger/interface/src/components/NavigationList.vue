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
  <q-list bordered>
    <q-item clickable v-ripple to="/" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="dashboard" color="secondary" />
      </q-item-section>
      <q-item-section>Dashboard</q-item-section>
    </q-item>
    <q-separator />

    <q-item-label header class="text-weight-bold text-uppercase">
      Harbinger data
    </q-item-label>

    <q-item clickable v-ripple to="/timeline" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="timeline" color="secondary" />
      </q-item-section>
      <q-item-section>Timeline</q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/situational_awareness" exact
      :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="travel_explore" color="secondary" />
      </q-item-section>
      <q-item-section>Situational Awareness</q-item-section>
      <q-item-section side v-if="data['situational_awareness'] > 0">
        <q-badge color="secondary" :label="data['situational_awareness']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/files" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="article" color="secondary" />
      </q-item-section>
      <q-item-section>Files</q-item-section>
      <q-item-section side v-if="data['file'] > 0">
        <q-badge color="secondary" :label="data['file']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/highlights" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="highlight" color="secondary" />
      </q-item-section>
      <q-item-section>Highlights</q-item-section>
      <q-item-section side v-if="data['highlight'] > 0">
        <q-badge color="secondary" :label="data['highlight']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/domains" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'"
      @mouseenter="showing = false">
      <q-item-section avatar>
        <q-icon name="corporate_fare" color="secondary" />
      </q-item-section>
      <q-item-section>Domains</q-item-section>
      <q-item-section side v-if="data['domain'] > 0">
        <q-badge color="secondary" :label="data['domain']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple exact :class="$q.dark.isActive ? 'text-white' : 'text-black'"
      @mouseenter="showing = true">
      <q-item-section avatar>
        <q-icon name="fingerprint" color="secondary" />
      </q-item-section>
      <q-item-section>
        Credentials
      </q-item-section>
      <q-item-section side v-if="credentials_total > 0">
        <q-badge color="secondary" :label="credentials_total" />
      </q-item-section>
      <q-item-section side>
        <q-icon name="chevron_right" color="secondary" />
      </q-item-section>
      <q-menu anchor="top end" self="top start" v-model="showing" @mouseleave="showing = false">
        <q-list>
          <q-item clickable v-ripple to="/credentials" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
            <q-item-section avatar>
              <q-icon name="fingerprint" color="secondary" />
            </q-item-section>
            <q-item-section>Credentials</q-item-section>
            <q-item-section side v-if="data['credential'] > 0">
              <q-badge color="secondary" :label="data['credential']" />
            </q-item-section>
          </q-item>
          <q-item clickable v-ripple to="/passwords" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
            <q-item-section avatar>
              <q-icon name="key" color="secondary" />
            </q-item-section>
            <q-item-section>Passwords</q-item-section>
            <q-item-section side v-if="data['password'] > 0">
              <q-badge color="secondary" :label="data['password']" />
            </q-item-section>
          </q-item>
          <q-item clickable v-ripple to="/kerberos" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
            <q-item-section avatar>
              <q-icon name="fas fa-dog" color="secondary" />
            </q-item-section>
            <q-item-section>Kerberos</q-item-section>
            <q-item-section side v-if="data['kerberos'] > 0">
              <q-badge color="secondary" :label="data['kerberos']" />
            </q-item-section>
          </q-item>
          <q-item clickable v-ripple to="/hashes" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
            <q-item-section avatar>
              <q-icon name="tag" color="secondary" />
            </q-item-section>
            <q-item-section>Hashes</q-item-section>
            <q-item-section side v-if="data['hash'] > 0">
              <q-badge color="secondary" :label="data['hash']" />
            </q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-item>

    <q-item clickable v-ripple to="/hosts" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'"
      @mouseenter="showing = false">
      <q-item-section avatar>
        <q-icon name="computer" color="secondary" />
      </q-item-section>
      <q-item-section>Hosts</q-item-section>
      <q-item-section side v-if="data['host'] > 0">
        <q-badge color="secondary" :label="data['host']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/shares" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'"
      @mouseenter="showing2 = false">
      <q-item-section avatar>
        <q-icon name="folder_shared" color="secondary" />
      </q-item-section>
      <q-item-section>Shares</q-item-section>
      <q-item-section side v-if="data['share'] > 0">
        <q-badge color="secondary" :label="data['share']" />
      </q-item-section>
    </q-item>
    <q-item clickable v-ripple exact :class="$q.dark.isActive ? 'text-white' : 'text-black'"
      @mouseenter="showing2 = true">
      <q-item-section avatar>
        <q-icon name="verified_user" color="secondary" />
      </q-item-section>
      <q-item-section>
        Certificates
      </q-item-section>
      <q-item-section side v-if="certificates_total > 0">
        <q-badge color="secondary" :label="certificates_total" />
      </q-item-section>
      <q-item-section side>
        <q-icon name="chevron_right" color="secondary" />
      </q-item-section>
      <q-menu anchor="top end" self="top start" v-model="showing2" @mouseleave="showing2 = false">
        <q-list>
          <q-item clickable v-ripple to="/certificate_authorities" exact
            :class="$q.dark.isActive ? 'text-white' : 'text-black'">
            <q-item-section avatar>
              <q-icon name="badge" color="secondary" />
            </q-item-section>
            <q-item-section>Authorities</q-item-section>
            <q-item-section side v-if="data['certificate_authority'] > 0">
              <q-badge color="secondary" :label="data['certificate_authority']" />
            </q-item-section>
          </q-item>
          <q-item clickable v-ripple to="/certificate_templates" exact
            :class="$q.dark.isActive ? 'text-white' : 'text-black'">
            <q-item-section avatar>
              <q-icon name="add_moderator" color="secondary" />
            </q-item-section>
            <q-item-section>Templates</q-item-section>
            <q-item-section side v-if="data['certificate_template'] > 0">
              <q-badge color="secondary" :label="data['certificate_template']" />
            </q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </q-item>

    <q-item clickable v-ripple to="/issues" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'"
      @mouseenter="showing2 = false">
      <q-item-section avatar>
        <q-icon name="priority_high" color="secondary" />
      </q-item-section>
      <q-item-section>Issues</q-item-section>
      <q-item-section side v-if="data['issue'] > 0">
        <q-badge color="secondary" :label="data['issue']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/labels" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'"
      @mouseenter="showing2 = false">
      <q-item-section avatar>
        <q-icon name="label" color="secondary" />
      </q-item-section>
      <q-item-section>Labels</q-item-section>
      <q-item-section side v-if="data['label'] > 0">
        <q-badge color="secondary" :label="data['label']" />
      </q-item-section>
    </q-item>

    <q-separator />

    <q-item-label header class="text-weight-bold text-uppercase">
      Jobs and Playbooks
    </q-item-label>

    <q-item clickable v-ripple to="/actions" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="check_circle" color="secondary" />
      </q-item-section>
      <q-item-section>Actions</q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/playbooks" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="menu_book" color="secondary" />
      </q-item-section>
      <q-item-section>Playbooks</q-item-section>
      <q-item-section side v-if="data['playbook'] > 0">
        <q-badge color="secondary" :label="data['playbook']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/proxy_jobs" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="share" color="secondary" />
      </q-item-section>
      <q-item-section>Socks Jobs</q-item-section>
      <q-item-section side v-if="data['proxy_job'] > 0">
        <q-badge color="secondary" :label="data['proxy_job']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/c2_jobs" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="fas fa-satellite-dish" color="secondary" />
      </q-item-section>
      <q-item-section>C2 Jobs</q-item-section>
      <q-item-section side v-if="data['c2_job'] > 0">
        <q-badge color="secondary" :label="data['c2_job']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/suggestions" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="fas fa-robot" color="secondary" />
      </q-item-section>
      <q-item-section>Suggestions</q-item-section>
      <q-item-section side v-if="data['suggestion'] > 0">
        <q-badge color="secondary" :label="data['suggestion']" />
      </q-item-section>
    </q-item>

    <q-separator />

    <q-item-label header class="text-weight-bold text-uppercase">
      C2 Connectors
    </q-item-label>

    <q-item clickable v-ripple to="/implants" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="fas fa-virus" color="secondary" />
      </q-item-section>
      <q-item-section>Implants</q-item-section>
      <q-item-section side v-if="data['c2_implant'] > 0">
        <q-badge color="secondary" :label="data['c2_implant']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/servers" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="dns" color="secondary" />
      </q-item-section>
      <q-item-section>C2 Servers</q-item-section>
      <q-item-section side v-if="data['c2_server'] > 0">
        <q-badge color="secondary" :label="data['c2_server']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/proxies" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="share" color="secondary" />
      </q-item-section>
      <q-item-section>Socks proxies</q-item-section>
      <q-item-section side v-if="data['proxy'] > 0">
        <q-badge color="secondary" :label="data['proxy']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/socks_servers" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="dns" color="secondary" />
      </q-item-section>
      <q-item-section>Socks servers</q-item-section>
      <!-- <q-item-section side v-if="c2_servers > 0">
        <q-badge color="secondary" :label="c2_servers" />
      </q-item-section> -->
    </q-item>

    <q-item clickable v-ripple to="/tasks" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="task" color="secondary" />
      </q-item-section>
      <q-item-section>Tasks</q-item-section>
      <q-item-section side v-if="data['c2_task'] > 0">
        <q-badge color="secondary" :label="data['c2_task']" />
      </q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/output" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="output" color="secondary" />
      </q-item-section>
      <q-item-section>Output</q-item-section>
    </q-item>

    <q-separator />

    <q-item-label header class="text-weight-bold text-uppercase">
      BloodHound
    </q-item-label>

    <q-item clickable v-ripple to="/bloodhound_utils" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="img:bloodhound.png" color="secondary" />
      </q-item-section>
      <q-item-section>Utils</q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/computers" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="computer" color="secondary" />
      </q-item-section>
      <q-item-section>Computers</q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/users" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="person" color="secondary" />
      </q-item-section>
      <q-item-section>Users</q-item-section>
    </q-item>

    <q-item clickable v-ripple to="/groups" exact :class="$q.dark.isActive ? 'text-white' : 'text-black'">
      <q-item-section avatar>
        <q-icon name="group" color="secondary" />
      </q-item-section>
      <q-item-section>Groups</q-item-section>
    </q-item>
  </q-list>
</template>

<script setup lang="ts">
import { useCounterStore } from 'src/stores/object-counters';
import { storeToRefs } from 'pinia';
import { ref, computed } from 'vue'

const store = useCounterStore();
const { data } = storeToRefs(store);

const showing = ref(false);
const showing2 = ref(false);

const credentials_total = computed(() =>
  store.get('credential') + store.get('password') + store.get('kerberos') + store.get('hash')
);

const certificates_total = computed(() =>
  store.get('certificate_template') + store.get('certificate_authority')
);

</script>
