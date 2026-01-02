<template>
  <div class="main-layout">
    <!-- 顶部导航栏 -->
    <Header />
    
    <!-- 主内容区 -->
    <main class="main-content">
      <AIToolsLayout v-if="moduleId === 'ai-tools'" />
      <AIToolsLayout v-else-if="moduleId === 'common-tools'" />
      <AIToolsLayout v-else-if="moduleId === 'works'" />
      <AIToolsLayout v-else />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Header from '../components/Header.vue'
import AIToolsLayout from './AIToolsLayout.vue'

const route = useRoute()

const moduleId = computed(() => route.params.moduleId as string)
</script>

<style scoped>
.main-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #ffffff;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: calc(100vh - 64px);
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .main-content {
    height: calc(100vh - 64px);
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .main-content {
    height: calc(100vh - 56px);
  }
}
</style>

