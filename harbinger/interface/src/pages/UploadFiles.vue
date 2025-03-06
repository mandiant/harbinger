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
    <q-card flat class="q-pa-md">
      <q-card-section>
        <h5>Upload multiple files</h5>
        <div class="row wrap justify-center items-stretch">
          <div class="col-md-10">
            <q-uploader
              url="upload_files/"
              auto-upload
              with-credentials
              multiple
              batch
              field-name="files"
              label="Drag and drop your files here, filetype will be auto detected."
              color="secondary"
            />
          </div>
        </div>
      </q-card-section>
    </q-card>
  </q-page>
</template>

<style scoped>
.q-uploader {
  height: fit-content;
  width: auto;
  max-height: none;
  height: 600px;
}
</style>

<script setup lang="ts">
import BreadCrumb from '../components/BreadCrumb.vue';
</script>
