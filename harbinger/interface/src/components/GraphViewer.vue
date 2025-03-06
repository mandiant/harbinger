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
  <q-card v-if="nodes">
    <q-card-section>Data from bloodhound</q-card-section>
    <v-chart
      v-if="nodes"
      class="chart"
      :option="option"
      autoresize
      style="height: 450px"
    ></v-chart>
  </q-card>
</template>

<script setup lang="ts">
import { toRefs, computed } from 'vue';
import { Node, Edge } from '../models';
import * as echarts from 'echarts/core';
import { GraphChart } from 'echarts/charts';
import { CanvasRenderer } from 'echarts/renderers';
import VChart from 'vue-echarts';

echarts.use([GraphChart, CanvasRenderer]);

const props = defineProps({
  nodes: {
    type: Array<Node>,
    default: [],
  },
  edges: {
    type: Array<Edge>,
    default: [],
  },
});

const { nodes, edges } = toRefs(props);

function getSymbol(labels: Array<string>) {
  const res = labels.filter((element) => element !== 'Base');
  switch (res[0]) {
    case 'Computer':
      return 'path://M528,0H48C21.5,0,0,21.5,0,48v320c0,26.5,21.5,48,48,48h192l-16,48h-72c-13.3,0-24,10.7-24,24s10.7,24,24,24h272c13.3,0,24-10.7,24-24s-10.7-24-24-24h-72l-16-48h192c26.5,0,48-21.5,48-48V48c0-26.5-21.5-48-48-48zm-16,352H64V64h448v288z';
    case 'User':
      return 'path://M224,256c70.7,0,128-57.3,128-128S294.7,0,224,0,96,57.3,96,128s57.3,128,128,128zm89.6,32h-16.7c-22.2,10.2-46.9,16-72.9,16s-50.6-5.8-72.9-16h-16.7C60.2,288,0,348.2,0,422.4V464c0,26.5,21.5,48,48,48h352c26.5,0,48-21.5,48-48v-41.6c0-74.2-60.2-134.4-134.4-134.4z';
    case 'Group':
      return 'path://M96,224c35.3,0,64-28.7,64-64s-28.7-64-64-64-64,28.7-64,64,28.7,64,64,64zm448,0c35.3,0,64-28.7,64-64s-28.7-64-64-64-64,28.7-64,64,28.7,64,64,64zm32,32h-64c-17.6,0-33.5,7.1-45.1,18.6,40.3,22.1,68.9,62,75.1,109.4h66c17.7,0,32-14.3,32-32v-32c0-35.3-28.7-64-64-64zm-256,0c61.9,0,112-50.1,112-112S381.9,32,320,32,208,82.1,208,144s50.1,112,112,112zm76.8,32h-8.3c-20.8,10-43.9,16-68.5,16s-47.6-6-68.5-16h-8.3C179.6,288,128,339.6,128,403.2V432c0,26.5,21.5,48,48,48h288c26.5,0,48-21.5,48-48v-28.8c0-63.6-51.6-115.2-115.2-115.2zm-223.7-13.4C161.5,263.1,145.6,256,128,256H64c-35.3,0-64,28.7-64,64v32c0,17.7,14.3,32,32,32h65.9c6.3-47.4,34.9-87.3,75.2-109.4z';
  }
  return 'path://M96,224c35.3,0,64-28.7,64-64s-28.7-64-64-64-64,28.7-64,64,28.7,64,64,64zm448,0c35.3,0,64-28.7,64-64s-28.7-64-64-64-64,28.7-64,64,28.7,64,64,64zm32,32h-64c-17.6,0-33.5,7.1-45.1,18.6,40.3,22.1,68.9,62,75.1,109.4h66c17.7,0,32-14.3,32-32v-32c0-35.3-28.7-64-64-64zm-256,0c61.9,0,112-50.1,112-112S381.9,32,320,32,208,82.1,208,144s50.1,112,112,112zm76.8,32h-8.3c-20.8,10-43.9,16-68.5,16s-47.6-6-68.5-16h-8.3C179.6,288,128,339.6,128,403.2V432c0,26.5,21.5,48,48,48h288c26.5,0,48-21.5,48-48v-28.8c0-63.6-51.6-115.2-115.2-115.2zm-223.7-13.4C161.5,263.1,145.6,256,128,256H64c-35.3,0-64,28.7-64,64v32c0,17.7,14.3,32,32,32h65.9c6.3-47.4,34.9-87.3,75.2-109.4z';
}

const option = computed(() => {
  const data: NonNullable<echarts.GraphSeriesOption['data']> = [];
  nodes.value.forEach((node: Node) => {
    data.push({
      id: node.id + '',
      name: node.name,
      symbol: getSymbol(node.labels),
      symbolSize: 40,
      itemStyle: {
        color: '#000',
      },
      label: {
        show: true,
        position: 'bottom',
      },
    });
  });

  const inner_edges: NonNullable<echarts.GraphSeriesOption['edges']> = [];
  edges.value.forEach((edge: Edge) => {
    inner_edges.push({
      source: edge.source + '',
      target: edge.target + '',
      name: edge.type,
      lineStyle: {
        width: 3,
        color: '#000',
      },
      label: {
        show: true,
        formatter: function (params) {
          return params.data.name;
        },
      },
    });
  });
  var option = {
    series: [
      {
        roam: true,
        draggable: true,
        type: 'graph',
        layout: 'force',
        animation: false,
        data: data,
        force: {
          repulsion: 200,
          edgeLength: 150,
        },
        edges: inner_edges,
        edgeSymbol: ['', 'arrow'],
      },
    ],
  };
  return option;
});
</script>
