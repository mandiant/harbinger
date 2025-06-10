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
  <q-btn flat color="secondary" @click="paste_clipboard" v-if="!readonly">Paste Clipboard</q-btn>

  <div ref="editorContainer" style="width: 100%; height: 30rem;"></div>
</template>

<style lang="scss">
.highlight {
  background: #006AFF;
}
</style>

<script setup lang="ts">
import { ref, toRefs, onMounted, onUpdated, watch } from 'vue';
import * as monaco from 'monaco-editor';

const props = defineProps({
  modelValue: {
    type: String,
    required: true,
  },
  readonly: {
    type: Boolean,
    default: false,
  },
  highlights: {
    type: Array<string>,
    default: [],
  },
  language: {
    type: String,
    default: 'text',
  },
});

const emit = defineEmits(['update:modelValue']);
const { modelValue, readonly, highlights, language } = toRefs(props);

const editorContainer = ref<HTMLElement | null>(null); // Use ref for the container
let editor: monaco.editor.IStandaloneCodeEditor | null = null;

const createMonaco = () => {
  if (!editorContainer.value) return; // Guard clause

  editor = monaco.editor.create(editorContainer.value, {
    value: modelValue.value,
    language: language.value,
    theme: 'vs-dark',
    minimap: { enabled: false },
    readOnly: readonly.value,
    automaticLayout: true, // Important for resizing and layout issues
  });

  const editorModel = editor.getModel();
  if (!editorModel) return;

  updateHighlights(editorModel); // Call highlight function here

  editorModel.onDidChangeContent(() => {
    const value = editorModel.getValue(); // More efficient than getLinesContent().join('\n')
    if (value !== modelValue.value) { // Compare directly to prop
      emit('update:modelValue', value);
    }
  });
  editor.focus();
};

function paste_clipboard() {
  navigator.clipboard.readText().then((result) => {
    if (editor) {
      editor.setValue(modelValue.value + result)
    }
  });
}

const updateHighlights = (editorModel: monaco.editor.ITextModel) => {
  editorModel.deltaDecorations([], highlights.value.flatMap((item: string) => {
    return editorModel.findMatches(item, false, false, false, null, false).map(match => ({
      range: match.range,
      options: {
        isWholeLine: false,
        inlineClassName: 'highlight'
      }
    }))
  }))
}


onMounted(() => {
  createMonaco();
});

onUpdated(() => {
  if (editor) {
    editor.updateOptions({ readOnly: readonly.value })
    const editorModel = editor.getModel();
    if (editorModel) {
      updateHighlights(editorModel)
    }
  }
})

watch(modelValue, (newValue) => {
  if (editor && editor.getValue() !== newValue) {
    editor.setValue(newValue)
  }
})


</script>