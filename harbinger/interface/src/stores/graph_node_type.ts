import { defineTypedStore, TypedStore } from 'src/stores/datastore';
import { GraphNodeType } from 'src/models';
import { computed } from 'vue';
import { storeToRefs } from 'pinia';

// Define the store configuration
const storeConfig = {
  pagination: {
    sortBy: 'name',
    descending: false,
    page: 1,
    rowsPerPage: 1000, // Assume there are fewer than 1000 node types to fetch them all at once
    rowsNumber: 0,
  },
};

// Create a singleton instance of the store
let storeInstance: TypedStore<GraphNodeType> | null = null;

/**
 * Returns a singleton instance of the GraphNodeType store.
 * The data is loaded automatically when the store is first accessed.
 */
export function getGraphNodeTypeStore() {
  if (!storeInstance) {
    storeInstance = defineTypedStore<GraphNodeType>('graph_node_types', storeConfig)();
    // Ensure data is loaded when the store is initialized
    storeInstance.LoadData();
  }
  return storeInstance;
}

/**
 * A composable function to access graph node type data and derived state.
 *
 * @returns An object with reactive properties for node types, loading state,
 *          a map of node types for quick lookups, and a function to reload the data.
 */
export function useGraphNodeTypes() {
    const store = getGraphNodeTypeStore();
    const { data: nodeTypes, loading } = storeToRefs(store);

    /**
     * A computed property that creates a Map for efficient lookup of node type
     * information (icon and color) by its name.
     */
    const nodeTypeMap = computed(() => {
        const map = new Map<string, { icon: string; color: string }>();
        for (const type of nodeTypes.value) {
            if (type.name && type.icon && type.color) {
                map.set(type.name, { icon: type.icon, color: type.color });
            }
        }
        return map;
    });

    return {
        nodeTypes,
        loading,
        nodeTypeMap,
        load: store.LoadData,
    };
}
