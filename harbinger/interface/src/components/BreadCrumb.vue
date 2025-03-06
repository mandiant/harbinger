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
  <div class="q-pa-md q-gutter-sm">
    <q-breadcrumbs>
      <q-breadcrumbs-el
        :icon="getIcon(route)"
        :to="route.path"
        v-for="route in routes"
        v-bind:key="route.name"
        :label="route?.meta.display_name"
        :class="$q.dark.isActive ? 'text-white' : 'text-black'"
      />
    </q-breadcrumbs>
  </div>
</template>

<script setup lang="ts">
import { RouteLocation, useRouter } from 'vue-router';
import { ref } from 'vue';

const $router = useRouter();

const routes = ref<Array<RouteLocation>>([]);

function LoadParent(routename: string) {
  let resolved = $router.resolve({ name: routename });
  if (resolved) {
    if (resolved.meta.parent) {
      if (resolved.meta.parent.toString() !== routename){
        LoadParent(resolved.meta.parent.toString());
      }
    }
    routes.value.push(resolved);
  }
}

if ($router.currentRoute.value.name) {
  LoadParent($router.currentRoute.value.name.toString());
}

function getIcon(route: RouteLocation) {
  if (route.meta.icon) {
    return route.meta.icon;
  }
  return 'home';
}
</script>
