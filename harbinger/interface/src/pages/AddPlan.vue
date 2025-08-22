//AddPlan.vue
<template>
  <q-page padding>
    <bread-crumb />
    <q-card>
      <q-card-section>
        <div class="text-h6">Create a new plan</div>
      </q-card-section>
      <q-card-section>
        <q-form @submit="onSubmit" @reset="onReset" class="q-gutter-md">
          <q-input
            filled
            v-model="form.name"
            label="Name"
            lazy-rules
            :rules="[(val) => (val && val.length > 0) || 'Please type something']"
          />
          <q-input
            filled
            v-model="form.objective"
            label="Objective"
            lazy-rules
            :rules="[(val) => (val && val.length > 0) || 'Please type something']"
          />

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
      </q-card-section>
    </q-card>
  </q-page>
</template>

<script setup lang="ts">
import { useQuasar } from 'quasar';
import { ref } from 'vue';
import { api } from 'boot/axios';
import { useRouter } from 'vue-router';
import BreadCrumb from 'src/components/BreadCrumb.vue';

const $q = useQuasar();
const loading = ref(false);
const $router = useRouter();

interface Form {
  name: string;
  objective: string;
}

const form = ref<Form>({
  name: '',
  description: '',
  objective: '',
});

function onSubmit() {
  loading.value = true;
  api
    .post('/plans/', form.value)
    .then((response) => {
      $q.notify({
        color: 'green-4',
        textColor: 'white',
        icon: 'cloud_done',
        position: 'top',
        message: `Submitted, plan_id: ${response.data.id}`,
      });
      $router.push({ name: 'plans' });
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
  form.value = {
    name: '',
    description: '',
    objective: '',
    status: 'INACTIVE',
  };
}
</script>
