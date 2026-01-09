<template>
  <div class="common-tools-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 常用工具模块布局 - 简单容器
</script>

<style scoped>
.common-tools-layout {
  @apply flex flex-col h-full overflow-hidden bg-gray-50;
}
</style>

