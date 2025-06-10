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
  <div class="q-pa-md">
    <q-card>
      <q-card-section class="row items-center justify-between">
        <div class="text-h6">SSH Terminal</div>
        <q-form @submit.prevent="connectSsh" class="q-gutter-md row items-center no-wrap">
          <q-btn
            type="submit"
            label="Connect SSH"
            color="primary"
            size="sm"
            :disable="connecting || isConnected || !jobId"
          />
          <q-btn
            @click="disconnectSsh"
            label="Disconnect"
            color="negative"
            size="sm"
            :disable="!isConnected"
          />
        </q-form>
      </q-card-section>

      <q-card-section class="q-pa-none">
        <!-- Terminal container with dynamic height for resizing -->
        <div
          ref="terminalContainer"
          class="terminal-container"
          :style="{ height: terminalHeight + 'px' }"
        >
          <!-- Resizer handle for drag-and-drop resizing -->
          <div
            class="resizer-handle"
            @mousedown="startResize"
          ></div>
        </div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebglAddon } from '@xterm/addon-webgl';
import { useQuasar } from 'quasar'; // Import Quasar's useQuasar composable for notifications

// --- Props Definition ---
interface Props {
  initialJobId?: string;
  initialSessionType?: 'interactive' | 'readonly';
  autoConnect?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  initialJobId: '',
  initialSessionType: 'interactive',
  autoConnect: false,
});

// --- Reactive State ---
const $q = useQuasar(); // Initialize Quasar notifications

const terminalContainer = ref<HTMLDivElement | null>(null);
const terminal = ref<Terminal | null>(null);
const fitAddon = ref<FitAddon | null>(null);
const webglAddon = ref<WebglAddon | null>(null); // Optional: If using WebglAddon
const socket = ref<WebSocket | null>(null);

const jobId = ref<string>(props.initialJobId);
const sessionType = ref<'interactive' | 'readonly'>(props.initialSessionType);
const connecting = ref<boolean>(false);
const isConnected = ref<boolean>(false);
const resizeTimeout = ref<number | null>(null);

// Reactive state for terminal height, allowing drag-and-drop resizing
const terminalHeight = ref<number>(400); // Initial height
const minTerminalHeight = 150; // Minimum height for the terminal
const isResizing = ref<boolean>(false); // Flag to indicate if resizing is in progress
let startY = 0; // Initial Y position of the mouse during resize
let startHeight = 0; // Initial height of the terminal during resize

// --- Methods ---

const initTerminal = () => {
  if (terminalContainer.value) {
    terminal.value = new Terminal({
      cursorBlink: true,
      fontFamily: 'monospace',
      fontSize: 14,
      theme: {
        background: '#000000',
        foreground: '#ffffff',
        cursor: '#ffffff',
        selectionBackground: '#424242',
      },
      scrollback: 5000,
    });

    fitAddon.value = new FitAddon();
    terminal.value.loadAddon(fitAddon.value);

    // Load WebglAddon for better performance if supported
    try {
      webglAddon.value = new WebglAddon();
      terminal.value.loadAddon(webglAddon.value);
    } catch (e) {
      console.warn('WebGL addon could not be loaded:', e);
      $q.notify({
        message: 'WebGL rendering not available, falling back to canvas.',
        color: 'warning',
        position: 'top'
      });
    }

    terminal.value.open(terminalContainer.value);
    // Ensure the terminal fits its current container size on initialization
    fitAddon.value.fit();

    // Handle data input from the terminal (user typing)
    terminal.value.onData(data => {
      if (socket.value && isConnected.value && socket.value.readyState === WebSocket.OPEN) {
        socket.value.send(data);
      }
    });

    // Handle terminal internal resize events (e.g., from fitAddon.fit() or manual resize)
    terminal.value.onResize(({ cols, rows }) => {
      console.log('onResize');
      // Only send resize event to backend if connected
      if (socket.value && isConnected.value && socket.value.readyState === WebSocket.OPEN) {
        socket.value.send(`RESIZE:${cols}:${rows}`);
      }
    });
  }
};

// Debounces the window resize event to prevent excessive calls to handleResize
const debounceResize = () => {
  if (resizeTimeout.value) {
    clearTimeout(resizeTimeout.value);
  }
  resizeTimeout.value = window.setTimeout(() => {
    handleResize();
  }, 200) as number;
};

// Handles the terminal resizing when the window resizes.
// This function is now responsible only for fitting the terminal to its container,
// regardless of the WebSocket connection state.
const handleResize = () => {
  if (terminal.value && fitAddon.value) {
    fitAddon.value.fit();
  }
};

// --- Resizing methods (drag and drop) ---
const startResize = (e: MouseEvent) => {
  isResizing.value = true;
  startY = e.clientY; // Get initial Y position of the mouse
  startHeight = terminalHeight.value; // Get initial height of the terminal
  // Add global event listeners for mouse move and up during resizing
  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', stopResize);
  e.preventDefault(); // Prevent default drag behavior
};

const onMouseMove = (e: MouseEvent) => {
  if (!isResizing.value) return;

  const newHeight = startHeight + (e.clientY - startY); // Calculate new height
  // Ensure the new height is not less than the minimum allowed height
  terminalHeight.value = Math.max(minTerminalHeight, newHeight);

  // After updating the container height, fit the terminal instance
  if (terminal.value && fitAddon.value) {
    fitAddon.value.fit();
  }
};

const messageCount = ref(0); // Add this reactive state

const stopResize = () => {
  isResizing.value = false;
  // Remove global event listeners after resizing stops
  window.removeEventListener('mousemove', onMouseMove);
  window.removeEventListener('mouseup', stopResize);
};

const connectSsh = () => {
  if (!jobId.value) {
    $q.notify({
      message: 'Please provide a Job ID.',
      color: 'warning'
    });
    return;
  }

  connecting.value = true;
  isConnected.value = false;
  terminal.value?.clear();
  terminal.value?.writeln('Attempting to connect to SSH...');

  let protocol = location.protocol.replace('http', 'ws');
  let ws_host = location.host;
  // Use import.meta.env for Vite environment variables
  if (import.meta.env.MODE === 'development') {
    ws_host = 'localhost:8000'; // Assuming your FastAPI backend runs on localhost:8000
  }
  const ws_url = `${protocol}//${ws_host}/ws/ssh/${sessionType.value}/${jobId.value}`;

  socket.value = new WebSocket(ws_url);

  socket.value.onopen = () => {
    console.log('WebSocket connected.');
    isConnected.value = true;
    connecting.value = false;
    terminal.value?.writeln('SSH connection established. Type away!');
  };

  socket.value.onmessage = (event: MessageEvent) => {
    terminal.value?.write(event.data);
    messageCount.value++;
    if (messageCount.value === 1) { // Or messageCount.value === 2 for two messages
      console.log('Received initial message(s). Sending resize command to backend.');
      if (terminal.value && fitAddon.value && socket.value) {
        socket.value.send(`RESIZE:${terminal.value.cols}:${terminal.value.rows}`);
      }
    }
  };

  socket.value.onclose = (event: CloseEvent) => {
    isConnected.value = false;
    connecting.value = false;
    let reason = event.reason || 'Connection closed';
    if (event.code === 1008) {
      reason = 'Authentication failed or token expired.';
    } else if (event.code === 1011) {
      reason = 'Server error occurred.';
    }
    // Only attempt to write to terminal if it still exists
    terminal.value?.writeln(`\r\nDisconnected from SSH: ${reason} (Code: ${event.code})`);
    console.log('WebSocket disconnected:', event.code, event.reason);
    // $q.notify({
    //   message: `Disconnected: ${reason} (Code: ${event.code})`,
    //   color: 'negative',
    //   position: 'top'
    // });
  };

  socket.value.onerror = (error: Event) => {
    isConnected.value = false;
    connecting.value = false;
    // Only attempt to write to terminal if it still exists
    terminal.value?.writeln('\r\nConnection error.');
    console.error('WebSocket error:', error);
    // $q.notify({
    //   message: 'WebSocket error. Check browser console and server logs.',
    //   color: 'negative',
    //   position: 'top'
    // });
  };
};

const disconnectSsh = () => {
  if (socket.value && socket.value.readyState === WebSocket.OPEN) {
    socket.value.close();
    socket.value = null;
  }
  isConnected.value = false;
  connecting.value = false;
};

// --- Lifecycle Hooks ---

onMounted(() => {
  initTerminal();
  // Add global resize listener with debouncing
  window.addEventListener('resize', debounceResize);

  // Attempt to auto-connect if configured
  if (props.autoConnect && props.initialJobId) {
    connectSsh();
  }
});

onBeforeUnmount(() => {
  // First, dispose of the terminal instance and its addons, and nullify their refs.
  // This is crucial to prevent further interactions with a disposed terminal.
  if (webglAddon.value) {
    try {
      webglAddon.value.dispose();
    } catch (error) {}
    webglAddon.value = null;
  }
  if (fitAddon.value) {
    try {
      fitAddon.value.dispose();
    } catch (error) {}
    fitAddon.value = null;
  }
  if (terminal.value) {
    try {
    terminal.value.dispose();
    } catch (error) {}
    terminal.value = null; // Set to null after disposal
  }

  // Clean up global resize listener
  window.removeEventListener('resize', debounceResize);
  // Remove resize event listeners if component unmounts while resizing
  window.removeEventListener('mousemove', onMouseMove);
  window.removeEventListener('mouseup', stopResize);

  // Ensure SSH connection is closed after terminal disposal.
  // The disconnectSsh function's terminal.value?.writeln calls will now safely do nothing.
  disconnectSsh();
});

// --- Watchers ---

// Watch for changes in initialJobId prop and potentially re-connect
watch(() => props.initialJobId, (newVal) => {
  jobId.value = newVal;
  if (props.autoConnect && newVal && !isConnected.value && !connecting.value) {
    connectSsh();
  }
});

// Watch for changes in initialSessionType prop and potentially re-connect
watch(() => props.initialSessionType, (newVal) => {
  sessionType.value = newVal;
  // Trigger connect if sessionType changes, autoConnect is true, and a jobId is present
  if (props.autoConnect && jobId.value && newVal && !isConnected.value && !connecting.value) {
    connectSsh();
  }
});
</script>

<style scoped>
.terminal-container {
  width: 100%;
  /* Height is now controlled by a reactive variable */
  background-color: black;
  color: white;
  padding: 10px;
  box-sizing: border-box;
  border: 1px solid #333;
  position: relative; /* Needed for absolute positioning of the resizer handle */
  overflow: hidden; /* Hide any overflow, especially during rapid resizing */
}

/* Resizer handle styling */
.resizer-handle {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 15px; /* Size of the handle */
  height: 15px; /* Size of the handle */
  background-color: #555; /* Handle color */
  cursor: se-resize; /* Cursor indicating resize direction */
  border-top-left-radius: 5px; /* Rounded corner for better aesthetics */
  z-index: 10; /* Ensure handle is on top of terminal content */
}

/* Ensure the xterm.js canvas fills the container */
/* Note: :deep is a Vue SFC feature for styling child components' internal elements */
.terminal-container :deep(.xterm .xterm-viewport) {
  overflow-y: auto; /* Enable vertical scrolling */
}

.terminal-container :deep(.xterm .xterm-screen) {
  height: 100% !important;
}
</style>
