<template>
  <div>
    <div class="q-pa-md row items-start q-gutter-md">
      <q-select v-model="selectedGraph" :options="graphOptions" label="Select a Graph" emit-value map-options
        class="col-3" />
    </div>

    <q-tabs v-model="tab" dense class="text-grey" active-color="primary" indicator-color="primary" align="justify"
      narrow-indicator>
      <q-tab name="visualization" label="Visualization" />
      <q-tab name="nodes" label="Nodes" />
      <q-tab name="edges" label="Edges" />
    </q-tabs>

    <q-separator />

    <q-tab-panels v-model="tab" animated>
      <q-tab-panel name="visualization">
        <div ref="container" style="height: 70vh; border: 1px solid #ccc; position: relative;"></div>
        <q-menu v-if="container" :target="container" touch-position context-menu>
          <q-list v-if="selectedNode" dense style="min-width: 150px;">
            <q-item>
              <q-item-section>
                <q-item-label header>Node Details</q-item-label>
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section>
                <q-item-label>Name</q-item-label>
                <q-item-label caption>{{ selectedNode.label }}</q-item-label>
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section>
                <q-item-label>Type</q-item-label>
                <q-item-label caption>{{ selectedNode.group }}</q-item-label>
              </q-item-section>
            </q-item>
            <q-item>
              <q-item-section>
                <q-item-label>ID</q-item-label>
                <q-item-label caption>{{ selectedNode.id }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
          <q-list v-else dense>
            <q-item>
              <q-item-section>No node selected.</q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </q-tab-panel>

      <q-tab-panel name="nodes">
        <q-table title="Nodes" :rows="nodes" :columns="nodeColumns" row-key="id" />
      </q-tab-panel>

      <q-tab-panel name="edges">
        <q-table title="Edges" :rows="edges" :columns="edgeColumns" row-key="id" />
      </q-tab-panel>
    </q-tab-panels>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed, watch, nextTick, onUnmounted } from 'vue';
import { Network } from 'vis-network/standalone';
import { DataSet } from 'vis-data/peer/esm/vis-data.js';
import { useQuasar, QTableProps } from 'quasar';
import { useGraphStore } from 'src/stores/graph';
import { storeToRefs } from 'pinia';
import { defineTypedStore } from 'src/stores/datastore';
import { Graph, GraphNode, GraphEdge } from 'src/models';

const $q = useQuasar();
const container = ref<HTMLElement | null>(null);
const tab = ref('visualization');
const selectedGraph = ref<string | null>(null);
const selectedNode = ref<any | null>(null);

const graphStore = useGraphStore();
const { nodes, edges } = storeToRefs(graphStore);

const graphListStore = defineTypedStore<Graph>('knowledge_graphs')();
const { data } = storeToRefs(graphListStore);

const graphOptions = computed(() => {
  return data.value.map(g => ({ label: g.name, value: g.id }));
});

const nodeColumns: QTableProps['columns'] = [
  { name: 'id', required: true, label: 'ID', align: 'left', field: 'id', sortable: true },
  { name: 'display_name', align: 'left', label: 'Display Name', field: 'display_name', sortable: true },
  { name: 'node_type', label: 'Type', field: 'node_type', sortable: true },
  {
    name: 'attributes',
    label: 'Attributes',
    field: (row) => JSON.stringify(row.attributes),
    sortable: false,
  },
];

const edgeColumns: QTableProps['columns'] = [
  { name: 'id', required: true, label: 'ID', align: 'left', field: 'id', sortable: true },
  { name: 'from', required: true, label: 'From', align: 'left', field: 'source_id', sortable: true },
  { name: 'to', required: true, label: 'To', align: 'left', field: 'target_id', sortable: true },
  { name: 'verb', label: 'Verb', field: 'verb', sortable: true },
  {
    name: 'attributes',
    label: 'Attributes',
    field: (row) => JSON.stringify(row.attributes),
    sortable: false,
  },
];

let network: Network | null = null;
const visNodes = new DataSet();
const visEdges = new DataSet();

const formatNode = (node: any) => {
  return {
    id: node.id,
    label: node.label,
    group: node.group,
    title: node.title,
    shape: 'icon',
    icon: {
      face: "'Material Icons'",
      code: node.icon,
      size: 50,
      color: node.color,
    },
    attributes: node.attributes,
  };
};

const formatEdge = (edge: GraphEdge) => {
  return {
    id: edge.id,
    from: edge.source_id,
    to: edge.target_id,
    label: edge.verb,
    arrows: 'to',
    attributes: edge.attributes,
  };
};

const initGraph = () => {
  if (!container.value) return;

  const options = {
    nodes: {
      shape: 'icon',
      font: {
        size: 14,
        face: 'mono-font',
        color: $q.dark.isActive ? 'white' : 'black',
      },
    },
    edges: {
      font: {
        size: 12,
        face: 'mono-font',
        color: $q.dark.isActive ? 'white' : 'black',
      },
    },
    physics: {
      forceAtlas2Based: {
        gravitationalConstant: -26,
        centralGravity: 0.005,
        springLength: 230,
        springConstant: 0.18,
      },
      maxVelocity: 146,
      solver: 'forceAtlas2Based',
      timestep: 0.35,
      stabilization: { iterations: 150 },
    },
  };
  network = new Network(container.value, { nodes: visNodes, edges: visEdges }, options);

  network.on('oncontext', (params) => {
    params.event.preventDefault();
    const nodeId = network.getNodeAt(params.pointer.DOM);
    if (nodeId) {
      selectedNode.value = visNodes.get(nodeId);
    } else {
      selectedNode.value = null;
    }
  });

  network.on('click', () => {
    selectedNode.value = null;
  });
};

onMounted(async () => {
  initGraph();
  await graphListStore.LoadData();
  if (graphOptions.value.length > 0 && !selectedGraph.value) {
    selectedGraph.value = graphOptions.value[0].value;
  }
});

onUnmounted(() => {
  graphStore.clearGraph();
  if (network) {
    network.destroy();
    network = null;
  }
  visNodes.clear();
  visEdges.clear();
});

watch(selectedGraph, async (newGraphId) => {
  if (newGraphId) {
    await graphStore.loadGraphData(newGraphId);
  } else {
    graphStore.clearGraph();
  }
});

watch([nodes, edges], ([newNodes, newEdges]) => {
  // Update nodes
  const formattedNodes = newNodes.map(formatNode);
  const nodeIdsInStore = new Set(formattedNodes.map(n => n.id));
  const nodesToRemove = visNodes.getIds().filter(id => !nodeIdsInStore.has(id));
  if (nodesToRemove.length > 0) {
    visNodes.remove(nodesToRemove);
  }
  visNodes.update(formattedNodes);

  // Update edges
  const formattedEdges = newEdges.map(formatEdge);
  const edgeIdsInStore = new Set(formattedEdges.map(e => e.id));
  const edgesToRemove = visEdges.getIds().filter(id => !edgeIdsInStore.has(id));
  if (edgesToRemove.length > 0) {
    visEdges.remove(edgesToRemove);
  }
  visEdges.update(formattedEdges);

}, { deep: true });

watch(tab, (newTab) => {
  if (newTab === 'visualization') {
    // To ensure the graph renders correctly when switching back to the tab,
    // we destroy the old instance and create a new one.
    nextTick(() => {
      if (network) {
        network.destroy();
        network = null;
      }
      initGraph();
    });
  }
});
</script>

