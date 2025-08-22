/**
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { defineStore } from 'pinia';
import { api } from 'boot/axios';
import { useGraphNodeTypes } from './graph_node_type';

// Define interfaces for Node and Edge based on what GraphVisualization.vue expects
interface GraphNode {
  id: string | number;
  label: string;
  group: string; // This is the node_type name
  icon?: string;
  color?: string;
  [key: string]: any;
}

interface GraphEdge {
  id: string | number;
  from: string | number;
  to: string | number;
  label?: string;
  [key: string]: any;
}

/**
 * Normalizes a node object from any source (API or WebSocket) to a consistent format.
 * Maps `node_type` to `group` and `display_name` to `label`.
 * @param node The raw node object.
 * @returns A normalized GraphNode object.
 */
function _normalizeNode(node: any): GraphNode {
    const normalized = { ...node };
    if (node.node_type && !node.group) {
        normalized.group = node.node_type;
    }
    if (node.display_name && !node.label) {
        normalized.label = node.display_name;
    }
    return normalized as GraphNode;
}


/**
 * Enriches a graph node with icon and color information from the node type map.
 * @param node The node to enrich.
 * @param nodeTypeMap A map of node type names to their icon and color.
 * @returns The enriched node.
 */
function _enrichNode(node: GraphNode, nodeTypeMap: Map<string, { icon: string; color: string }>): GraphNode {
    const typeInfo = nodeTypeMap.get(node.group); // 'group' holds the node_type
    return {
        ...node,
        icon: typeInfo?.icon || 'help_outline', // Default icon
        color: typeInfo?.color || '#9E9E9E',   // Default color (grey)
    };
}


export const useGraphStore = defineStore('graph', {
  state: () => ({
    selectedGraphId: null as string | null,
    nodes: [] as GraphNode[],
    edges: [] as GraphEdge[],
    loading: false,
  }),
  getters: {
    getNodes: (state) => state.nodes,
    getEdges: (state) => state.edges,
  },
  actions: {
    async loadGraphData(graphId: string) {
      if (this.selectedGraphId === graphId && this.nodes.length > 0) {
        return;
      }
      this.loading = true;
      this.selectedGraphId = graphId;

      // Ensure node types are loaded before processing graph data
      const { nodeTypeMap, load: loadNodeTypes } = useGraphNodeTypes();
      await loadNodeTypes();

      try {
        const response = await api.get(`/knowledge_graphs/${graphId}/visualize`);
        this.nodes = response.data.nodes.map((node: any) => {
            const normalized = _normalizeNode(node);
            return _enrichNode(normalized, nodeTypeMap.value);
        });
        this.edges = response.data.edges;
      } catch (error) {
        console.error('Error fetching graph data:', error);
        this.nodes = [];
        this.edges = [];
      } finally {
        this.loading = false;
      }
    },
    // Actions to handle websocket events
    addNode(node: any) {
      const normalizedNode = _normalizeNode(node);
      const { nodeTypeMap } = useGraphNodeTypes();
      const enrichedNode = _enrichNode(normalizedNode, nodeTypeMap.value);
      if (!this.nodes.some(n => n.id === enrichedNode.id)) {
        this.nodes.push(enrichedNode);
      }
    },
    updateNode(node: any) {
      const normalizedNode = _normalizeNode(node);
      const { nodeTypeMap } = useGraphNodeTypes();
      const enrichedNode = _enrichNode(normalizedNode, nodeTypeMap.value);
      const index = this.nodes.findIndex(n => n.id === enrichedNode.id);
      if (index !== -1) {
        this.nodes[index] = { ...this.nodes[index], ...enrichedNode };
      } else {
        this.addNode(enrichedNode);
      }
    },
    deleteNode(nodeId: string | number) {
      this.nodes = this.nodes.filter(n => n.id !== nodeId);
      this.edges = this.edges.filter(e => e.from !== nodeId && e.to !== nodeId);
    },
    addEdge(edge: GraphEdge) {
      if (!this.edges.some(e => e.id === edge.id)) {
        this.edges.push(edge);
      }
    },
    updateEdge(edge: GraphEdge) {
      const index = this.edges.findIndex(e => e.id === edge.id);
      if (index !== -1) {
        this.edges[index] = { ...this.edges[index], ...edge };
      } else {
        this.addEdge(edge);
      }
    },
    deleteEdge(edgeId: string | number) {
      this.edges = this.edges.filter(e => e.id !== edgeId);
    },
    clearGraph() {
        this.selectedGraphId = null;
        this.nodes = [];
        this.edges = [];
    }
  },
});
