<template>
  <div class="welcome-message">
    <h2 class="welcome-title">{{ welcomeTitle }}</h2>
    <p class="welcome-text">{{ welcomeText }}</p>
  </div>
</template>

<script setup lang="ts">
// 写死的欢迎语数据
const welcomeTitle = '欢迎使用 AI 工具平台'
const welcomeText = '我是你的AI助手，可以帮助你处理各种任务。请告诉我你需要什么帮助？'
</script>

<style scoped>
.welcome-message {
  text-align: center;
  padding: 48px 24px;
  max-width: 600px;
  margin: 0 auto;
}

.welcome-title {
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
  letter-spacing: -0.5px;
}

.welcome-text {
  font-size: 15px;
  color: #6b7280;
  line-height: 1.7;
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

