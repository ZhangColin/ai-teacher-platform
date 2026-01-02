<template>
  <div class="common-tools-layout">
    <div class="coming-soon-container">
      <div class="coming-soon-content">
        <div class="coming-soon-icon">
          <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <h2 class="coming-soon-title">开发中，敬请期待……</h2>
        <p class="coming-soon-description">常用工具模块正在开发中，我们将尽快为您提供更多实用工具。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 常用工具模块布局（开发中）
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

