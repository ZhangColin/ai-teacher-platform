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
  display: flex;
  align-items: center;
  gap: 4px;
  background-color: #f3f4f6;
  padding: 4px;
  border-radius: 12px;
}

.module-button {
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  background-color: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.module-button:hover {
  background-color: rgba(255, 255, 255, 0.8);
  color: #1f2937;
}

.module-button.active {
  background-color: #ffffff;
  color: #1f2937;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
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

