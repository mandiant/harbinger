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
  <q-card flat>
    <q-tree no-transition :nodes="simple" node-key="id" @lazy-load="onLazyLoad">
      <template v-slot:default-header="prop">
        <q-item dense class="col-grow">
          <q-item-section avatar>
            <q-icon :name="prop.node.icon" />
          </q-item-section>
          <q-item-section>
            <q-item-label>
              <template v-if="prop.node.label">{{ prop.node.label }}</template>
              <template v-else>{{ prop.node.props.unc_path }}</template>
            </q-item-label>
            <q-item-label caption>
              <template v-if="prop.node.props.type !== 'dir' && prop.node.props.size > 0">
                {{ prettyBytes(prop.node.props.size) }}
              </template>
            </q-item-label>
          </q-item-section>
          <q-item-section side top>
            <labels-list readonly object-type="share_file" :object-id="prop.node.id" v-model="prop.node.props.labels"/>
          </q-item-section>
        </q-item>
      </template>
    </q-tree>
  </q-card>
</template>

<script setup lang='ts'>
import { toRefs, ref, computed } from 'vue';
import { ShareFile } from 'src/models';
import useloadData from 'src/load-data';
import { QTreeNode } from 'quasar';
import { api } from 'src/boot/axios';
import { useQuasar } from 'quasar';
import prettyBytes from 'pretty-bytes';
import LabelsList from './LabelsList.vue';

const $q = useQuasar();

const props = defineProps({
  share_id: {
    type: String,
    required: true,
  }
});


const { share_id } = toRefs(props);

const { loading, data, loadData, AddFilter } =
  useloadData<Array<ShareFile>>('share_files');

AddFilter({ share_id: share_id.value });
AddFilter({ depth: 0 })


const search = ref('');

AddFilter({ search: search.value });

loadData();

const simple = computed(() => {
  let nodes: Array<QTreeNode> = []
  data.value.forEach((element) => {
    nodes.push({
      label: element.name,
      icon: element.type === 'dir' ? (element.indexed ? 'folder' : 'folder_open') : 'description',
      children: [],
      lazy: element.type === 'dir',
      id: element.id,
      props: element
    })
  })
  return nodes
}
);

const stuff = {
  page: 1,
  size: 100,
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function onLazyLoad({ node, key, done, fail }) {
  const filters = {
    parent_id: node.id,
  }
  loading.value = true
  api.get('/share_files/', { params: { ...filters, ...stuff } }).then((response) => {
    let data: Array<QTreeNode> = []
    response.data.items.forEach((element: ShareFile) => {
      data.push({
        label: element.name,
        icon: element.type === 'dir' ? (element.indexed ? 'folder' : 'folder_open') : 'description',
        children: [],
        lazy: element.type === 'dir',
        id: element.id,
        props: element,
      })
    })
    done(data)
    loading.value = false
  }).catch((error) => {
    $q.notify({
      color: 'negative',
      position: 'top',
      message: `Unable load objects: ${error.data}`,
      icon: 'report_problem',
    });
    fail()
    loading.value = false
  })
}

</script>
