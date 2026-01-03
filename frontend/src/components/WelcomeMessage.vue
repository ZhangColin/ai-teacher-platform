<template>
  <div class="welcome-message">
    <h2 class="welcome-title">{{ welcomeTitle }}</h2>
    <p class="welcome-text">{{ welcomeText }}</p>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  welcomeMessage?: string
}>()

// 如果没有传入欢迎语，使用默认值
const welcomeTitle = '欢迎使用 AI 工具平台'
const welcomeText = props.welcomeMessage || '我是你的AI助手，可以帮助你处理各种任务。请告诉我你需要什么帮助？'
</script>

<style scoped>
.welcome-message {
  @apply text-center py-16 px-6 max-w-2xl mx-auto; /* 从py-12(48px)增加到py-16(64px)，更大气 */
}

.welcome-title {
  @apply text-3xl font-semibold text-gray-900 mb-4;
  letter-spacing: -0.5px;
}

.welcome-text {
  @apply text-base text-gray-500 leading-relaxed;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .welcome-message {
    padding: 40px 20px;
  }
  
  .welcome-title {
    font-size: 26px;
  }
  
  .welcome-text {
    font-size: 15px;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .welcome-message {
    padding: 32px 16px;
  }
  
  .welcome-title {
    font-size: 24px;
  }
  
  .welcome-text {
    font-size: 14px;
  }
}
</style>
