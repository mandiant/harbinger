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
    <q-card flat class="q-pa-md" v-if="!plan && loading">
      <q-card-section>
        <q-skeleton type="text" class="text-h6" />
        <q-skeleton type="text" class="text-caption" />
      </q-card-section>
      <q-card-section>
        <q-skeleton type="text" />
        <q-skeleton type="text" class="text-caption" />
      </q-card-section>
    </q-card>
    <q-card flat class="q-pa-md" v-if="plan">
      <q-card-section>
        <div class="row items-center justify-between">
          <div>
            <div class="row items-center q-gutter-sm">
              <q-item-label class="text-h6">{{ plan.name }}</q-item-label>
              <llm-status-indicator :status="plan.llm_status">
                <q-tooltip>LLM Agent Status: {{ plan.llm_status }}</q-tooltip>
              </llm-status-indicator>
            </div>
            <q-item-label caption :class="$q.dark.isActive ? 'text-white' : 'text-black'">
              Status: {{ plan.status }}
            </q-item-label>
          </div>
          <div class="row items-center q-gutter-sm">
            <q-btn-group flat>
              <q-btn
                size="sm"
                icon="toc"
                :flat="!showPlanSteps"
                @click="showPlanSteps = !showPlanSteps"
              >
                <q-tooltip>{{ showPlanSteps ? 'Hide' : 'Show' }} Plan Steps</q-tooltip>
              </q-btn>
              <q-btn
                size="sm"
                icon="terminal"
                :flat="!showSupervisorLogs"
                @click="showSupervisorLogs = !showSupervisorLogs"
              >
                <q-tooltip>{{ showSupervisorLogs ? 'Hide' : 'Show' }} Supervisor Logs</q-tooltip>
              </q-btn>
            </q-btn-group>
            <q-separator vertical class="q-mx-sm" />
            <!-- <q-toggle
              v-model="allowAll"
              @update:model-value="toggleAllowAll"
              label="Auto-Approve"
              left-label
            >
              <q-tooltip>Automatically approve all suggested actions</q-tooltip>
            </q-toggle> -->
            <q-btn size="sm" color="primary" @click="startPlan" icon="play_arrow" v-if="plan.llm_status === 'INACTIVE'">
              <q-tooltip>Start Plan</q-tooltip>
            </q-btn>
            <q-btn
              size="sm"
              color="secondary"
              @click="forceUpdate"
              icon="sync"
              v-if="plan.llm_status === 'MONITORING' || plan.llm_status === 'PROCESSING'"
              :disable="plan.llm_status === 'PROCESSING'"
            >
              <q-tooltip>Force Update (Disabled while processing)</q-tooltip>
            </q-btn>
            <q-btn size="sm" color="negative" @click="terminatePlan" icon="stop" v-if="plan.llm_status === 'MONITORING' || plan.llm_status === 'PROCESSING'">
              <q-tooltip>Terminate Plan</q-tooltip>
            </q-btn>
          </div>
        </div>
      </q-card-section>
      <q-card-section>
        <p>{{ plan.description }}</p>
        <div class="text-caption text-grey">
          Created: {{ new Date(plan.time_created).toLocaleString() }} | Last Updated: {{ new Date(plan.time_updated).toLocaleString() }}
        </div>
      </q-card-section>
    </q-card>
    <div class="row q-col-gutter-md q-mt-md">
      <div :class="columnClass" v-if="showPlanSteps">
        <q-card flat bordered class="full-height">
          <q-card-section class="row items-center justify-between q-py-sm">
            <div class="text-h6">Plan Steps</div>
            <div>
              <q-btn
                v-if="planStepListRef"
                flat
                dense
                size="sm"
                :icon="planStepListRef.allExpanded ? 'unfold_less' : 'unfold_more'"
                @click="planStepListRef.toggleAll"
              >
                <q-tooltip>{{ planStepListRef.allExpanded ? 'Collapse All' : 'Expand All' }}</q-tooltip>
              </q-btn>
              <q-btn flat dense size="sm" icon="refresh" @click="planStepListRef?.refresh()">
                <q-tooltip>Refresh</q-tooltip>
              </q-btn>
            </div>
          </q-card-section>
          <q-separator />
          <q-card-section class="q-pa-none">
            <plan-step-list :plan-id="id" ref="planStepListRef" />
          </q-card-section>
        </q-card>
      </div>
      <div :class="columnClass" v-if="showSupervisorLogs">
        <q-card flat bordered class="full-height">
          <q-card-section class="row items-center justify-between q-py-sm">
            <div class="text-h6">Supervisor Logs</div>
            <div>
              <q-btn
                v-if="llmLogViewerRef"
                flat
                dense
                size="sm"
                :icon="llmLogViewerRef.allExpanded ? 'unfold_less' : 'unfold_more'"
                @click="llmLogViewerRef.toggleAll"
              >
                <q-tooltip>{{ llmLogViewerRef.allExpanded ? 'Collapse All' : 'Expand All' }}</q-tooltip>
              </q-btn>
              <q-btn flat dense size="sm" icon="refresh" @click="llmLogViewerRef?.refresh()">
                <q-tooltip>Refresh</q-tooltip>
              </q-btn>
            </div>
          </q-card-section>
          <q-separator />
          <llm-log-viewer :plan-id="id" ref="llmLogViewerRef" style="height: calc(80vh - 48px);"/>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, toRefs, watch, computed } from 'vue';
import { useQuasar } from 'quasar';
import { api } from 'boot/axios';
import { Plan } from '../models';
import BreadCrumb from '../components/BreadCrumb.vue';
import PlanStepList from '../components/PlanStepList.vue';
import LlmStatusIndicator from '../components/LlmStatusIndicator.vue';
import LlmLogViewer from 'src/components/LlmLogViewer.vue';
import { defineTypedStore } from 'src/stores/datastore';

const $q = useQuasar();
const props = defineProps({
  id: {
    type: String,
    required: true
  },
});

const { id } = toRefs(props);
const loading = ref(false);
const allowAll = ref(false);
const showPlanSteps = ref(true);
const showSupervisorLogs = ref(true);

const planStepListRef = ref<InstanceType<typeof PlanStepList> | null>(null);
const llmLogViewerRef = ref<InstanceType<typeof LlmLogViewer> | null>(null);

const columnClass = computed(() => {
  if (showPlanSteps.value && showSupervisorLogs.value) {
    return 'col-6';
  }
  return 'col-12';
});

const usePlanStore = defineTypedStore<Plan>('plans');
const planStore = usePlanStore();

const plan = ref<Plan>();

watch(() => planStore.getItemFromCache(id.value), (newPlanData) => {
  if (newPlanData) {
    plan.value = { ...newPlanData };
  }
}, { deep: true });

async function loadPlan(force = false) {
  loading.value = true;
  try {
    const planData = await planStore.loadById(id.value, force);
    if (planData) {
      plan.value = { ...planData };
    }
  } catch (error) {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: 'Loading failed',
      icon: 'report_problem',
    });
  } finally {
    loading.value = false;
  }
}

watch(id, () => loadPlan(), { immediate: true });

async function startPlan() {
  if (!plan.value) return;
  try {
    await api.post(`/plans/${plan.value.id}/start_supervisor`);
    $q.notify({
      color: 'positive',
      position: 'top',
      message: `Starting supervisor for plan ${plan.value.name}`,
      icon: 'play_arrow',
    });
    await loadPlan(true);
  } catch (error) {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: 'Failed to start supervisor',
      icon: 'report_problem',
    });
  }
}

async function terminatePlan() {
  if (!plan.value) return;
  try {
    await api.post(`/plans/${plan.value.id}/stop_supervisor`);
    $q.notify({
      color: 'negative',
      position: 'top',
      message: `Terminating supervisor for plan ${plan.value.name}`,
      icon: 'stop',
    });
    await loadPlan(true);
  } catch (error) {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: 'Failed to stop supervisor',
      icon: 'report_problem',
    });
  }
}

async function forceUpdate() {
  if (!plan.value) return;
  try {
    await api.post(`/plans/${plan.value.id}/force_update`);
    $q.notify({
      color: 'info',
      position: 'top',
      message: 'Force update signal sent',
      icon: 'sync',
    });
  } catch (error) {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: 'Failed to send force update signal',
      icon: 'report_problem',
    });
  }
}

function toggleAllowAll(value: boolean) {
  $q.notify({
    color: 'info',
    position: 'top',
    message: `Auto-approval ${value ? 'enabled' : 'disabled'} for plan ${plan.value?.name}`,
    icon: value ? 'check_circle' : 'cancel',
  });
  // TODO: Implement actual logic to update the plan's auto-approval status
}
</script>
