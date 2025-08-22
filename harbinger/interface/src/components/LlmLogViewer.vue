<template>
  <div class="llm-log-viewer" ref="logContainer">
    <q-list bordered separator>
      <q-item v-for="log in logs" :key="log.id" :class="$q.dark.isActive ? 'text-white' : 'text-black'">
        <q-item-section avatar>
          <q-icon :name="logTypeIcon(log.log_type)" />
        </q-item-section>

        <q-item-section>
          <q-item-label caption>{{ formatTimestamp(log.time_created) }}</q-item-label>
          <div v-if="log.log_type === 'REASONING'">
            {{ log.content.summary }}
          </div>
          <div v-if="log.log_type === 'TOOL_CALL'">
            <q-expansion-item
              v-model="expansionState[log.id]"
              :label="`Tool Call: ${log.content.tool_name}`"
              dense
              header-class="tool-call-header"
            >
              <q-card>
                <q-card-section class="q-pa-sm">
                  <pre>{{ formatArguments(log.content.arguments) }}</pre>
                </q-card-section>
              </q-card>
            </q-expansion-item>
          </div>
        </q-item-section>
      </q-item>
    </q-list>
    <div class="row justify-center q-mt-md">
      <q-pagination
        v-if="totalPages > 1"
        v-model="currentPage"
        :max="totalPages"
        direction-links
        flat
        dense
        size="sm"
        @update:model-value="onPageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { QList, QItem, QItemSection, QIcon, QItemLabel, QExpansionItem, QCard, QCardSection, useQuasar, QPaginaton } from 'quasar';
import { api } from 'boot/axios';

// 1. DATA STRUCTURES
interface LlmLog {
  id: string;
  plan_id: string;
  time_created: string;
  log_type: 'REASONING' | 'TOOL_CALL';
  content: {
    summary?: string;
    tool_name?: string;
    arguments?: Record<string, any>;
  };
}

// 2. PROPS
const props = defineProps<{
  planId: string;
}>();

// 3. STATE
const $q = useQuasar();
const logs = ref<LlmLog[]>([]);
let socket: WebSocket | null = null;
const expansionState = ref<Record<string, boolean>>({});
const currentPage = ref(1);
const pageSize = ref(20);
const totalPages = ref(0);

// 4. COMPUTED
const toolCallLogs = computed(() => logs.value.filter(log => log.log_type === 'TOOL_CALL'));
const allExpanded = computed(() => {
  if (toolCallLogs.value.length === 0) return false;
  return toolCallLogs.value.every(log => expansionState.value[log.id]);
});


// 5. DATA FETCHING AND REAL-TIME CONNECTION
const fetchHistoricalLogs = async (page = 1) => {
  if (!props.planId) return;
  try {
    const response = await api.get('/llm_logs/', {
      params: {
        plan_id: props.planId,
        page: page,
        size: pageSize.value,
      }
    });
    logs.value = response.data.items;
    totalPages.value = response.data.pages;
    currentPage.value = response.data.page;
  } catch (error) {
    console.error('Failed to fetch historical logs:', error);
    // TODO: Add user-facing error notification
  }
};

const onPageChange = (newPage: number) => {
  fetchHistoricalLogs(newPage);
};

const setupWebSocket = () => {
  if (!props.planId) return;

  let protocol = location.protocol.replace('http', 'ws');
  let ws_host = location.host;
  // Use import.meta.env for Vite environment variables
  if (import.meta.env.MODE === 'development') {
    ws_host = 'localhost:8000'; // Assuming your FastAPI backend runs on localhost:8000
  }
  const wsUrl = `${protocol}//${ws_host}/ws/plans/${props.planId}/llm_logs`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log('WebSocket connection established for LLM logs.');
  };

  socket.onmessage = (event) => {
    try {
      const newLog = JSON.parse(event.data) as LlmLog;
      // If on the first page, prepend the new log. Otherwise, do nothing.
      if (currentPage.value === 1) {
        logs.value.unshift(newLog);
        // Optional: Trim the logs array if it exceeds pageSize
        if (logs.value.length > pageSize.value) {
          logs.value.pop();
        }
      } else {
        // If not on the first page, you might want to indicate that new logs are available.
        // For now, we just refresh the current page to avoid complexity.
        fetchHistoricalLogs(currentPage.value);
      }
    } catch (error) {
      console.error('Failed to parse incoming log message:', error);
    }
  };

  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
    // TODO: Add user-facing error notification
  };

  socket.onclose = () => {
    console.log('WebSocket connection closed.');
    // Optional: Implement reconnection logic here
  };
};

// 6. UI LOGIC
const toggleAll = () => {
  const expand = !allExpanded.value;
  toolCallLogs.value.forEach(log => {
    expansionState.value[log.id] = expand;
  });
};

function refresh() {
  fetchHistoricalLogs(currentPage.value);
}

const logTypeIcon = (logType?: string) => {
  if (logType === 'REASONING') return 'psychology';
  if (logType === 'TOOL_CALL') return 'build';
  return 'help_outline';
}
const formatTimestamp = (timestamp: string) => new Date(timestamp).toLocaleString();
const formatArguments = (args: Record<string, any> | string | undefined) => {
  if (!args) return '';
  try {
    const parsed = typeof args === 'string' ? JSON.parse(args) : args;
    return JSON.stringify(parsed, null, 2);
  } catch (e) {
    // If parsing fails, return the original string
    return String(args);
  }
};

// 7. LIFECYCLE HOOKS
onMounted(async () => {
  await fetchHistoricalLogs();
  setupWebSocket();
});

onUnmounted(() => {
  if (socket) {
    socket.close();
  }
});

defineExpose({
  toggleAll,
  refresh,
  allExpanded,
});

</script>

<style lang="scss" scoped>
.llm-log-viewer {
  height: 100%;
  overflow-y: auto;
  border: 1px solid $grey-4;
  border-radius: 4px;
}

.tool-call-header {
  font-weight: bold;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: $grey-2;
  padding: 10px;
  border-radius: 4px;
  font-size: 0.8em;
}

/* Dark Mode Styles */
.body--dark {
  .llm-log-viewer {
    border-color: $grey-8;
  }

  pre {
    background-color: $grey-9;
    border: 1px solid $grey-8;
  }
}
</style>
