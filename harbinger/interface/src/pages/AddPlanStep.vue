//AddPlanStep.vue
<template>
<q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">

    
    <q-input filled v-model="form.plan_id" label="plan_id" />
    <q-input filled v-model="form.playbook_step_id" label="playbook_step_id" />
    <q-input filled v-model="form.number" label="number" />
    <q-input filled v-model="form.status" label="status" />
    <q-input filled v-model="form.time_created" label="time_created" />
    <q-input filled v-model="form.time_updated" label="time_updated" />

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
        color="secondary"
        flat
        class="q-ml-sm"
    />
    </div>
</q-form>
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

plan_id: string;
playbook_step_id: string;
number: number;
status: string;
time_created: string;
time_updated: string;
}

const form = ref<Form>({} as Form);

function onSubmit() {
    api
    .post('/plan_steps/', form.value)
    .then((response) => {
        $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        position: 'top',
        message: `Submitted, plan_steps_id: ${response.data.id}`,
        });
        $router.push({ name: 'plan_steps' });
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
