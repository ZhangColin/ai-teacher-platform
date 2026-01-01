<template>
  <div class="app-container">
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  line-height: 1.5;
  color: #1f2937;
  background-color: #ffffff;
}

.app-container {
  min-height: 100vh;
}
</style>
