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
    <bread-crumb />
    <q-card flat class="q-pa-md">
      <q-card-section>
        <h5>Add a label</h5>
        <q-form @submit="onSubmit" class="q-gutter-md">
        <q-input filled v-model="name" label="Name" />
        <q-select
          label="Category"
          filled
          :options="categories"
          v-model="category"
          use-input
          hide-dropdown-icon
          input-debounce="0"
          new-value-mode="add-unique"
        />
        <q-btn :style="{ background: hex }" text-color="black" class="q-mb-sm" @click="pickcolor = true">
          {{ hex }}
        </q-btn>
        <q-btn class="q-mb-sm" @click="randomizeHex()">Random color</q-btn>
        <div>
            <q-btn
              label="Submit"
              type="submit"
              color="secondary"
              :loading="loading"
            />
            <q-btn
              label="Reset"
              type="reset"
              color="seconday"
              flat
              class="q-ml-sm"
            />
          </div>
        </q-form>
      </q-card-section>
    </q-card>
    <q-dialog v-model="pickcolor">
      <q-card style="width: 400px">
        <q-card-section>
          <div class="text-h6">Choose a color</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-color v-model="hex" class="my-picker" />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="OK" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useQuasar } from 'quasar';
import BreadCrumb from '../components/BreadCrumb.vue';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';

const $q = useQuasar();
const $router = useRouter();

const hex = ref('#ffffff')
const pickcolor = ref(false)
const name = ref('')
const category = ref('')
const loading = ref(false);

const categories = ref([]);

function randomizeHex() {
  hex.value = '#' + [...Array(6)].map(() => Math.floor(Math.random() * 16).toString(16)).join('')
}

randomizeHex()

function loadCategories() {
  api.get('/label_categories/').then((response) => {
    categories.value = response.data
  }).catch(() => {
    $q.notify({
        color: 'negative',
        position: 'top',
        message: 'Loading of categories failed',
        icon: 'report_problem',
      });
  })
}

loadCategories()

function onSubmit() {
  loading.value = true;
  api
    .post('/labels/', {
      name: name.value,
      category: category.value,
      color: hex.value
    })
    .then(() => {
      loading.value = false;
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        message: 'Created label',
        position: 'top',
      });
      $router.push({ name: 'labels'});
    })
    .catch((error) => {
      loading.value = false;
      $q.notify({
        color: 'negative',
        position: 'top',
        message: `Creating failed: ${error.response.data}`,
        icon: 'report_problem',
      });
    });
}

</script>
