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
    <q-card flat class="column col-xl-3 col-lg-4 col-md-6 col-sm-8 col-xs-12">
        <q-card-section>
            <q-item>
                <q-item-section avatar>
                    <q-icon :name="icon" size="4em" />
                </q-item-section>
                <q-item-section>
                    <q-item-label>{{ name }}</q-item-label>
                </q-item-section>
            </q-item>
        </q-card-section>
        <q-card-section class="col-grow">
            <q-item clickable @click="loadData()" v-for="entry in data" v-bind:key="entry.key">
                <q-item-section avatar v-if="entry.icon">
                    <q-icon :name="entry.icon" size="md" />
                </q-item-section>
                <q-item-section>{{ entry.key }}</q-item-section>
                <q-item-section side>{{ entry.value }}</q-item-section>
            </q-item>
            <q-inner-loading :showing="loading">
                <q-spinner-gears size="50px" color="secondary" />
            </q-inner-loading>
        </q-card-section>
        <q-card-actions class="self-end">
            <q-btn v-for="link in to" v-bind:key="link.to" icon="open_in_new" flat color="secondary" :to="link.to"
                :label="link.label" />
        </q-card-actions>
    </q-card>
</template>

<script setup lang="ts">
import { toRefs } from 'vue';
import useloadData from 'src/load-data';
import { Statistic, StatisticLink } from '../models';

const props = defineProps({
    url: {
        type: String,
        required: true,
    },
    icon: {
        type: String,
        required: true,
    },
    name: {
        type: String,
        required: true,
    },
    to: {
        type: Array<StatisticLink>,
        required: true,
    }
});

const { url, icon, name, to } = toRefs(props);

const { loading, data, loadData } =
    useloadData<Array<Statistic>>(url.value);
loadData();
</script>
