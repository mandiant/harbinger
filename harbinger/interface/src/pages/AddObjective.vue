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
            <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
                <q-input filled v-model="form.name" label="name" />
                <q-input filled v-model="form.description" label="description" />
                <q-input filled v-model="form.status" label="status" />
                <div>
                    <q-btn label="Submit" type="submit" color="secondary" :loading="loading" />
                    <q-btn label="Reset" type="reset" color="secondary" flat class="q-ml-sm" />
                </div>
            </q-form>
        </q-card>
    </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref } from 'vue';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';

const $q = useQuasar();
const loading = ref(false);
const $router = useRouter();

interface Form {
    name: string;
    description: string;
    status: string;
}

const form = ref<Form>({} as Form);

function onSubmit() {
    api
        .post('/objectives/', form.value)
        .then((response) => {
            $q.notify({
                color: 'green-4',
                textColor: 'white',
                icon: 'cloud_done',
                position: 'top',
                message: `Submitted, objective_id: ${response.data.id}`,
            });
            $router.push({ name: 'objectives' });
            loading.value = false;
        })
        .catch(() => {
            loading.value = false;
            $q.notify({
                color: 'negative',
                position: 'top',
                message: 'Creation failed',
                icon: 'report_problem',
            });
        });
}

function onReset() {
    form.value = {} as Form;
}
</script>
