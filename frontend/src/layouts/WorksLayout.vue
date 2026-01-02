<template>
  <div class="works-layout">
    <div class="coming-soon-container">
      <div class="coming-soon-content">
        <div class="coming-soon-icon">
          <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        <h2 class="coming-soon-title">开发中，敬请期待……</h2>
        <p class="coming-soon-description">作品展示模块正在开发中，我们将尽快为您展示精彩作品。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 作品展示模块布局（开发中）
</script>

<style scoped>
.works-layout {
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

