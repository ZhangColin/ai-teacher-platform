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
  color: theme('colors.gray.800');
  /* 层级0：页面主背景 - 极浅灰，带微妙渐变，避免纯白刺眼 */
  background: linear-gradient(to bottom, theme('colors.gray.50') 0%, theme('colors.gray.100') 100%);
  min-height: 100vh;
}

.app-container {
  min-height: 100vh;
}
</style>
