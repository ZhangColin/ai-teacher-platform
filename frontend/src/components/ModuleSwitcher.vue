<template>
  <div class="module-switcher">
    <!-- 加载状态 -->
    <div v-if="navigationStore.loading" class="loading-placeholder">
      <div class="skeleton-button" v-for="i in 3" :key="i"></div>
    </div>
    
    <!-- 模块按钮 -->
    <button
      v-else
      v-for="module in modules"
      :key="getModuleId(module)"
      :class="['module-button', { active: currentModule === getModuleId(module) }]"
      @click="handleModuleClick(getModuleId(module))"
    >
      {{ module.name }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNavigationStore } from '../stores/navigationStore'

const route = useRoute()
const router = useRouter()
const navigationStore = useNavigationStore()

// 从导航配置获取模块列表
const modules = computed(() => navigationStore.modules)

const currentModule = computed(() => route.params.moduleId as string || 'ai-tools')

function getModuleId(module: any) {
  return navigationStore.getModuleId(module)
}

function handleModuleClick(moduleId: string) {
  router.push(`/modules/${moduleId}`)
}
</script>

<style scoped>
.module-switcher {
  @apply flex items-center gap-1 bg-gray-100 p-1 rounded-xl;
}

.module-button {
  @apply px-5 py-2 text-sm font-medium text-gray-500 bg-transparent border-none rounded-lg cursor-pointer transition-all duration-200 whitespace-nowrap;
  /* 添加更柔和的hover效果 */
}

.module-button:hover {
  @apply bg-white/80 text-gray-800;
  transform: translateY(-1px);
}

.module-button.active {
  @apply bg-white text-gray-900 font-semibold;
  /* 层级3：交互层 - 白色背景，轻微阴影，添加更明显的视觉反馈 */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
}

.module-button:active {
  transform: translateY(0);
}

/* 加载占位符 */
.loading-placeholder {
  @apply flex gap-1;
}

.skeleton-button {
  @apply w-20 h-8 bg-gray-200 rounded-lg animate-pulse;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .module-switcher {
    gap: 2px;
    padding: 3px;
  }
  
  .module-button {
    padding: 6px 14px;
    font-size: 13px;
  }
}
</style>

