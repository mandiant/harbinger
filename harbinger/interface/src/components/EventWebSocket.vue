<template>
  <q-icon color="green" name="wifi" v-if="store.connected">
    <q-tooltip v-if="store.connected">Event websocket is connected</q-tooltip>
  </q-icon>
  <q-btn flat v-else>
    <q-spinner-gears />
    <q-tooltip>Connecting to the websocket</q-tooltip>
  </q-btn>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue';
import { useCounterStore } from 'src/stores/object-counters';
import { useLabelStore } from 'src/stores/labels';
import { useFileStore } from 'src/stores/files';
import { useMythicImplantStore } from 'src/stores/mythic_implants'
import { useMetaStore } from 'src/stores/meta';
import { useProgressStore } from 'src/stores/progress'
import {
  PostgresEventPayload,
  C2Implant, C2Task, C2Job, C2Server, Domain,
  Password, Credential, Proxy, ProxyJob, Component,
  File, Host, Kerberos, SituationalAwareness,
  Share, Hash, CertificateTemplate, CertificateAuthority, Issue, Action,
  C2ServerType, Progress, Chain, Highlight, Suggestion, Checklist, Objective,
  Process, PlaybookTemplate, C2ServerStatus,
  ParseResult, Setting, SocksServer,
  C2ServerArguments,
  C2Output,
  Plan,
  PlanStep,
} from '../models';
import { useMeta } from 'quasar'
import { defineTypedStore, TypedStore, BaseModel } from 'src/stores/datastore';

// --- Store Initialization ---
const connection = ref<WebSocket | null>(null);
const store = useCounterStore();
const label_store = useLabelStore();
const file_store = useFileStore();
const c2_implant_store = useMythicImplantStore();
const progress_store = useProgressStore();
const meta = useMetaStore();

const storeMap = new Map<string, TypedStore<any>>();

// === Define Typed Stores ===
storeMap.set('domains', defineTypedStore<Domain>('domains')());
storeMap.set('passwords', defineTypedStore<Password>('passwords')());
storeMap.set('kerberos', defineTypedStore<Kerberos>('kerberos')());
storeMap.set('credentials', defineTypedStore<Credential>('credentials')());
storeMap.set('proxies', defineTypedStore<Proxy>('proxies')());
storeMap.set('input_files', defineTypedStore<File>('input_files')());
storeMap.set('proxy_jobs', defineTypedStore<ProxyJob>('proxy_jobs')());
storeMap.set('components', defineTypedStore<Component>('components')());
storeMap.set('proxy_job_output', defineTypedStore<ProxyJob>('proxy_job_output')());
storeMap.set('files', defineTypedStore<File>('files')());
storeMap.set('hosts', defineTypedStore<Host>('hosts')());
storeMap.set('processes', defineTypedStore<Process>('processes')());
storeMap.set('playbook_templates', defineTypedStore<PlaybookTemplate>('templates/playbooks')());
storeMap.set('shares', defineTypedStore<Share>('shares')());
storeMap.set('share_files', defineTypedStore<any>('share_files')());
storeMap.set('highlights', defineTypedStore<Highlight>('highlights')());
storeMap.set('hashes', defineTypedStore<Hash>('hashes')());
storeMap.set('parse_results', defineTypedStore<ParseResult>('parse_results')());
storeMap.set('settings', defineTypedStore<Setting>('settings')());
storeMap.set('socks_servers', defineTypedStore<SocksServer>('socks_servers')());
storeMap.set('actions', defineTypedStore<Action>('actions')());
storeMap.set('issues', defineTypedStore<Issue>('issues')());
storeMap.set('suggestions', defineTypedStore<Suggestion>('suggestions')());
storeMap.set('checklist', defineTypedStore<Checklist>('checklist')());
storeMap.set('objectives', defineTypedStore<Objective>('objectives')());

// C2 related:
storeMap.set('c2_jobs', defineTypedStore<C2Job>('c2_jobs')());
storeMap.set('c2_servers', defineTypedStore<C2Server>('c2_servers')());
storeMap.set('c2_server_status', defineTypedStore<C2ServerStatus>('c2_server_status')());
storeMap.set('c2_implants', defineTypedStore<C2Implant>('c2_implants')());
storeMap.set('c2_tasks', defineTypedStore<C2Task>('c2_tasks')());
storeMap.set('c2_task_output', defineTypedStore<C2Output>('c2_task_output')());
storeMap.set('c2_server_types', defineTypedStore<C2ServerType>('c2_server_types')());
storeMap.set('c2_server_arguments', defineTypedStore<C2ServerArguments>('c2_server_arguments')());

// Playbook related:
storeMap.set('playbooks', defineTypedStore<Chain>('playbooks')());
storeMap.set('playbook_step', defineTypedStore<any>('playbook_step')());
storeMap.set('playbook_step_modifier', defineTypedStore<any>('playbook_step_modifier')());
storeMap.set('plan', defineTypedStore<Plan>('plans')());
storeMap.set('plan_step', defineTypedStore<PlanStep>('plan_steps')());

// Certificate related:
storeMap.set('certificate_authorities', defineTypedStore<CertificateAuthority>('certificate_authorities')());
storeMap.set('certificate_templates', defineTypedStore<CertificateTemplate>('certificate_templates')());

// Other:
storeMap.set('situational_awareness', defineTypedStore<SituationalAwareness>('situational_awareness')());


// --- Reconnection State ---
const reconnectAttempts = ref(0);
const maxReconnectAttempts = 20; // Increased max attempts for longer recovery scenarios
const initialReconnectDelay = 1000; // 1 second
const maxReconnectDelay = 10000; // 60 seconds (1 minute)
let connectionTimeoutTimer: number | null = null; // To hold the timeout ID
const CONNECT_TIMEOUT_MS = 5000; // 10 seconds for connection attempt timeout

// --- Helper function to pluralize singular key prefixes ---
function pluralizeTableName(singularKeyPrefix: string): string {
  switch (singularKeyPrefix) {
    case 'process': return 'processes';
    case 'ip_address': return 'ip_addresses';
    case 'analysis': return 'analyses';
    case 'c2_task': return 'c2_tasks';
    case 'c2_job': return 'c2_jobs';
    case 'playbook': return 'playbooks';
    case 'file': return 'files';
    case 'hash': return 'hashes';
    case 'issue': return 'issues';
    case 'objective': return 'objectives';
    case 'component': return 'components';
    case 'action': return 'actions';
    case 'c2_implant': return 'c2_implants';
    case 'proxy_job': return 'proxy_jobs';
    case 'proxy_job_output': return 'proxy_job_output';
    case 'share_file': return 'share_files';
    case 'socks_server': return 'socks_servers';
    case 'certificate_authority': return 'certificate_authorities';
    case 'certificate_template': return 'certificate_templates';
    case 'manual_timeline_task': return 'manual_timeline_tasks';
    case 'suggestion': return 'suggestions';
    case 'checklist': return 'checklist';
    case 'highlight': return 'highlights';
    case 'parse_result': return 'parse_results';
    case 'setting_category': return 'setting_category';
    case 'setting': return 'settings';
    case 'c2_server_type': return 'c2_server_types';
    case 'c2_server_argument': return 'c2_server_arguments';
    case 'c2_implant_type': return 'c2_implant_types';
    case 'c2_implant_argument': return 'c2_implant_arguments';
    case 'certificate_template_authority_map': return 'certificate_template_authority_map';
    case 'certificate_template_permission': return 'certificate_template_permissions';
    case 'action_playbook': return 'action_playbook';
    case 'c2_server_status': return 'c2_server_status';
  }

  if (singularKeyPrefix.endsWith('s')) {
    return singularKeyPrefix;
  }
  if (singularKeyPrefix.endsWith('y')) {
    return singularKeyPrefix.slice(0, -1) + 'ies';
  }
  return singularKeyPrefix + 's';
}

const validMappedTableNames = new Set<string>(Array.from(storeMap.keys()));
validMappedTableNames.add('labels');
validMappedTableNames.add('labeled_item');
validMappedTableNames.add('progress_bars');


// --- WebSocket Connection Logic ---
function CreateWebSocket() {
  // Clear any existing connection timeout timer before starting a new attempt
  if (connectionTimeoutTimer !== null) {
      clearTimeout(connectionTimeoutTimer);
      connectionTimeoutTimer = null;
  }

  // Prevent new connection if already connected or connecting
  if (connection.value && (connection.value.readyState === WebSocket.OPEN || connection.value.readyState === WebSocket.CONNECTING)) {
      return;
  }

  let protocol = location.protocol.replace('http', 'ws');
  let ws_url = `${protocol}//${location.host}/events`;

  if (process.env.NODE_ENV === 'development') {
    ws_url = `${protocol}//localhost:8000/events`;
  }

  console.log(`Attempting to connect to WebSocket: ${ws_url}`);
  store.setDisconnected(); // Set to disconnected state while connecting

  connection.value = new WebSocket(ws_url);

  // --- Implement a manual connection timeout ---
  connectionTimeoutTimer = setTimeout(() => {
    if (connection.value && connection.value.readyState === WebSocket.CONNECTING) {
      console.warn(`WebSocket connection timed out after ${CONNECT_TIMEOUT_MS / 1000} seconds.`);
      // Force close the connection attempt, which will trigger onclose
      connection.value.close(4000, 'Connection timed out'); // Use a custom code for timeout
    }
  }, CONNECT_TIMEOUT_MS) as unknown as number; // Cast to number for clearTimeout

  connection.value.onmessage = function (event) {
    try {
      const data: PostgresEventPayload = JSON.parse(event.data);
      const tableName = data.table_name;
      const operation = data.operation;

      if (tableName === 'labels') {
          label_store.loadLabels();
          if (operation === 'insert') {
            store.incrementObject(tableName);
          }
          return;
      }

      if (tableName === 'labeled_item') {
          const labeledItemData = (data.after || data.before) as any;
          if (!labeledItemData) {
              console.warn('Received malformed labeled_item event:', data);
              return;
          }

          const relatedObjectKeys = [
              'domain_id', 'password_id', 'kerberos_id', 'credential_id', 'proxy_id',
              'proxy_job_id', 'proxy_job_output', 'file_id', 'playbook_id', 'playbook_step_id',
              'c2_job_id', 'host_id', 'process_id', 'playbook_template_id', 'c2_server_id',
              'c2_implant_id', 'c2_task_id', 'c2_task_output_id', 'share_id', 'share_file_id',
              'highlight_id', 'hash_id', 'parse_result_id', 'socks_server_id', 'action_id',
              'certificate_authority_id', 'certificate_template_id', 'issue_id',
              'manual_timeline_task_id', 'suggestion_id', 'checklist_id', 'objective_id',
              'plan_id', 'plan_step_id',
          ];

          for (const key of relatedObjectKeys) {
              const relatedObjectId = labeledItemData[key];
              if (relatedObjectId !== undefined && relatedObjectId !== null) {
                  let singularKeyPrefix: string;
                  let actualTableName: string;

                  singularKeyPrefix = key.replace('_id', '');

                  if (key === 'proxy_job_output') actualTableName = 'proxy_job_output';
                  else if (key === 'checklist_id') actualTableName = 'checklist';
                  else actualTableName = pluralizeTableName(singularKeyPrefix);

                  if (!validMappedTableNames.has(actualTableName)) {
                    console.warn(`[labeled_item event] Derived table name '${actualTableName}' from FK '${key}' is not a recognized or mapped table. Skipping update for this related item.`);
                    continue;
                  }

                  const relatedStore = storeMap.get(actualTableName);
                  if (relatedStore) {
                      relatedStore.updateCache(relatedObjectId);

                      if (actualTableName === 'c2_implants') {
                          c2_implant_store.ReLoadAliveImplants();
                      }
                      if (actualTableName === 'files') {
                        file_store.loadFiles();
                      }
                  } else {
                      console.warn(`[labeled_item event] No Pinia store instance found for table: '${actualTableName}' (derived from FK '${key}'). This indicates a missing storeMap.set.`);
                  }
              }
          }
          if (operation === 'insert') {
              store.incrementObject(tableName);
          }
          return;
      }

      if (tableName === 'progress_bars') {
        const progressData: Progress = data.after || data.before;
        if (!progressData || progressData.id === undefined) {
            console.warn('Received malformed progress event (missing ID):', data);
            return;
        }
        if (operation === 'update') {
          progress_store.UpdateProgress(progressData.id, progressData.current, progressData.percentage);
        } else if (operation === 'insert') {
          progress_store.AddProgress(progressData);
        } else if (operation === 'delete') {
          progress_store.DeleteProgress(progressData.id);
        }
        return;
      }

      if (tableName === 'proxy_jobs') {
        if (operation === 'update') {
          const storeInstance = storeMap.get('proxy_jobs')
          if (storeInstance) {
            const updatedObject: BaseModel = data.after;
            storeInstance.loadById(updatedObject.id, true)
            return;
          }
        }
      }

      const storeInstance = storeMap.get(tableName);
      if (storeInstance) {
          if (operation === 'insert' && data.after) {
              const newObject: BaseModel = data.after;
              if (newObject.id !== undefined) {
                storeInstance.addObject(newObject);
                store.incrementObject(tableName);
              } else {
                console.warn(`Received insert for ${tableName} without an ID:`, data);
              }
          } else if (operation === 'update' && data.after) {
              const updatedObject: BaseModel = data.after;
              if (updatedObject.id !== undefined) {
                storeInstance.updateObject(updatedObject);
              } else {
                console.warn(`Received update for ${tableName} without an ID:`, data);
              }
          } else if (operation === 'delete' && data.before) {
              const deletedObject: BaseModel = data.before;
              if (deletedObject && deletedObject.id !== undefined) {
                 storeInstance.deleteObject(deletedObject.id);
              } else {
                 console.warn(`Received delete for ${tableName} without valid ID in 'before' data:`, data);
              }
          }
      } else {
          console.warn(`No Pinia store mapped for table_name: '${tableName}'. Event not processed.`);
      }

    } catch (e) {
      console.error('Failed to parse WebSocket message or handle event:', e);
    }
  };

  connection.value.onopen = function () {
    // Clear the timeout if the connection opens successfully
    if (connectionTimeoutTimer !== null) {
      clearTimeout(connectionTimeoutTimer);
      connectionTimeoutTimer = null;
    }
    console.log('WebSocket connected!');
    store.setConnected();
    reconnectAttempts.value = 0; // Reset attempts on successful connection
    label_store.loadLabels();
    file_store.loadFiles();
    file_store.loadFileTypes();
    c2_implant_store.ReLoadAliveImplants();
    progress_store.loadProgressBars();
  };

  connection.value.onerror = function (error) {
    console.error('WebSocket Error:', error);
    // The onerror event typically precedes a close event.
    // The onclose handler will then manage the reconnection logic.
  };

  connection.value.onclose = function (event) {
    // Clear any pending connection timeout if the connection closes for any reason
    if (connectionTimeoutTimer !== null) {
        clearTimeout(connectionTimeoutTimer);
        connectionTimeoutTimer = null;
    }

    console.log(`WebSocket closed: Code=${event.code}, Reason=${event.reason}`);
    store.setDisconnected();

    // Only attempt to reconnect if the component is still mounted and we haven't hit max attempts
    if (reconnectAttempts.value < maxReconnectAttempts) {
        reconnectAttempts.value++;
        const delay = Math.min(
            initialReconnectDelay * Math.pow(2, reconnectAttempts.value - 1),
            maxReconnectDelay
        );
        console.log(`Attempting to reconnect in ${delay / 1000} seconds (attempt ${reconnectAttempts.value})...`);
        setTimeout(() => {
            // Ensure CreateWebSocket is only called if the component is still relevant
            // and the previous connection attempt (if any) is fully closed.
            if (connection.value?.readyState === WebSocket.CLOSED || !connection.value) {
                CreateWebSocket();
            }
        }, delay);
    } else {
        console.warn('Max WebSocket reconnection attempts reached. Giving up.');
        // Consider showing a more prominent error to the user here (e.g., "Cannot connect to server. Please try again later.")
    }
  };
}

// Initial connection attempt
CreateWebSocket();

onUnmounted(() => {
  // When component unmounts, stop further reconnection attempts
  reconnectAttempts.value = maxReconnectAttempts; // Effectively disables further retries
  if (connectionTimeoutTimer !== null) {
      clearTimeout(connectionTimeoutTimer);
      connectionTimeoutTimer = null;
  }
  if (connection.value && connection.value.readyState === WebSocket.OPEN) {
    connection.value.close(); // Close active connection gracefully
  }
});

useMeta(() => {
  return {
    title: meta.title
  }
})
</script>
