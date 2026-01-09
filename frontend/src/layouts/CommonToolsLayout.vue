<template>
  <div class="common-tools-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 常用工具模块布局
</script>

<style scoped>
.common-tools-layout {
  @apply flex items-center justify-center h-full w-full;
  background-color: theme('colors.gray.50');
}

.coming-soon-container {
  @apply text-center px-6 py-12;
  max-width: 600px;
}

.coming-soon-content {
  @apply flex flex-col items-center gap-6;
}

.coming-soon-icon {
  @apply text-gray-400;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.coming-soon-title {
  @apply text-2xl font-semibold text-gray-900;
  letter-spacing: -0.5px;
}

.coming-soon-description {
  @apply text-base text-gray-500 leading-relaxed;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .coming-soon-container {
    padding: 40px 24px;
  }
  
  .coming-soon-title {
    font-size: 22px;
  }
  
  .coming-soon-description {
    font-size: 15px;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .coming-soon-container {
    padding: 32px 20px;
  }
  
  .coming-soon-icon {
    width: 56px;
    height: 56px;
  }
  
  .coming-soon-title {
    font-size: 20px;
  }
  
  .coming-soon-description {
    font-size: 14px;
  }
}
</style>

