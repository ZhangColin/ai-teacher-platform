<template>
  <div class="module-switcher">
    <button
      v-for="module in modules"
      :key="module.id"
      :class="['module-button', { active: currentModule === module.id }]"
      @click="handleModuleClick(module.id)"
    >
      {{ module.name }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 写死的模块数据
const modules = [
  { id: 'ai-tools', name: 'AI工具' },
  { id: 'common-tools', name: '常用工具' },
  { id: 'works', name: '作品展示' },
]

const currentModule = computed(() => route.params.moduleId as string || 'ai-tools')

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

