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
                <h5>Add an entry to the timeline</h5>
                <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
                    <q-input filled v-model="form.command_name" label="Command" />
                    <q-input filled v-model="form.arguments" label="Arguments" />
                    <q-input filled v-model="form.status" label="Status" />
                    <q-input filled v-model="form.hostname" label="Hostname" />
                    <q-input filled v-model="form.operator" label="Operator" />
                    <q-input type="textarea" autogrow filled v-model="form.output" label="Output" />
                    <h6>Time started</h6>
                    <div class="q-gutter-md row items-start">
                        <q-date label="Time started" v-model="form.time_started" mask="YYYY-MM-DD HH:mm"
                            color="secondary" />
                        <q-time label="Time started" v-model="form.time_started" mask="YYYY-MM-DD HH:mm" format24h
                            color="secondary" />
                    </div>
                    <h6>Time completed</h6>
                    <div class="q-gutter-md row items-start">
                        <q-date label="Time completed" v-model="form.time_completed" mask="YYYY-MM-DD HH:mm"
                            color="secondary" />
                        <q-time label="Time completed" v-model="form.time_completed" mask="YYYY-MM-DD HH:mm" format24h
                            color="secondary" />
                    </div>
                    <div>
                        <q-btn label="Submit" type="submit" color="secondary" :loading="loading" />
                        <q-btn label="Reset" type="reset" color="secondary" flat class="q-ml-sm" />
                    </div>
                </q-form>
            </q-card-section>
        </q-card>
    </q-page>
</template>

<script setup lang="ts">
import BreadCrumb from 'src/components/BreadCrumb.vue';
import { useQuasar } from 'quasar';
import { ref } from 'vue';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';
import { date } from 'quasar'


const $q = useQuasar();
const loading = ref(false);
const $router = useRouter();

interface Form {
    time_created: string;
    status: string;
    arguments: string;
    time_started: string;
    time_completed: string;
    command_name: string;
    operator: string;
    output: string;
    hostname: string;
}

const timeStamp = Date.now()
const formattedString = date.formatDate(timeStamp, 'YYYY-MM-DD HH:mm')

const form = ref<Form>({ time_started: formattedString, time_completed: formattedString, status: 'completed' } as Form);

function onSubmit() {
    api
        .post('/manual_timeline_tasks/', form.value)
        .then((response) => {
            $q.notify({
                color: 'green-4',
                textColor: 'white',
                icon: 'cloud_done',
                position: 'top',
                message: `Submitted, id: ${response.data.id}`,
            });
            $router.push({ name: 'timeline' });
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
    form.value = { time_started: formattedString, time_completed: formattedString, status: 'completed' } as Form as Form;
}
</script>