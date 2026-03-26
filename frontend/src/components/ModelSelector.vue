<template>
  <div class="model-selector" ref="selectorRef">
    <!-- 当前模型显示 -->
    <button
      @click="toggleDropdown"
      class="model-button"
      :class="{ 'is-open': isOpen }"
      :title="currentModelDisplay"
    >
      <svg class="model-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM16.5 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L9.75 12l2.846-.813a4.5 4.5 0 003.09-3.09L16.5 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L22.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
      </svg>
      <span class="model-name">{{ currentModelDisplay }}</span>
      <svg class="dropdown-icon" :class="{ 'is-open': isOpen }" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
      </svg>
    </button>

    <!-- 模型下拉列表 -->
    <transition name="dropdown">
      <div v-if="isOpen" class="model-dropdown">
        <div class="model-list" v-if="!loading">
          <button
            v-for="model in availableModels"
            :key="model.id"
            @click="selectModel(model.id)"
            class="model-option"
            :class="{ 'is-selected': sessionStore.currentModel === model.id || isDefaultModel(model.id) }"
          >
            <div class="model-option-content">
              <span class="model-option-name">{{ model.name }}</span>
              <span class="model-option-provider">{{ model.provider }}</span>
              <span class="model-option-description">{{ model.description }}</span>
            </div>
            <svg v-if="sessionStore.currentModel === model.id || isDefaultModel(model.id)" class="check-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          </button>
        </div>
        <div v-else class="loading-state">
          加载中...
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useSessionStore } from '../stores/sessionStore'
import { ApiService } from '../services/apiClient'
import type { ModelListItem, ToolListItem } from '../types'

const sessionStore = useSessionStore()
const isOpen = ref(false)
const selectorRef = ref<HTMLElement | null>(null)
const availableModels = ref<ModelListItem[]>([])
const loading = ref(false)
const defaultModel = ref<string | null>(null)
const currentTool = ref<ToolListItem | null>(null)

// 当前模型显示名称
const currentModelDisplay = computed(() => {
  const currentModel = sessionStore.currentModel
  if (!currentModel) {
    // 如果没有手动选择模型，显示默认模型
    if (defaultModel.value) {
      const model = availableModels.value.find(m => m.id === defaultModel.value)
      return model ? model.name : defaultModel.value
    }
    return '默认模型'
  }
  const model = availableModels.value.find(m => m.id === currentModel)
  return model ? model.name : currentModel
})

// 判断是否是默认模型
function isDefaultModel(modelId: string): boolean {
  return !sessionStore.currentModel && modelId === defaultModel.value
}

// 根据工具获取所需的 AI 能力
function getRequiredCapability(tool: ToolListItem | null): string | null {
  if (!tool) {
    console.log('[ModelSelector] 工具为空，将加载所有模型')
    return null  // 返回 null 表示不过滤，加载所有模型
  }

  // 优先使用工具配置的 required_capability
  if (tool.required_capability) {
    console.log('[ModelSelector] 使用工具配置的能力:', tool.required_capability)
    return tool.required_capability
  }

  // 兼容旧数据：根据 content_type 和 media_type 推导能力
  console.log('[ModelSelector] 工具未配置能力，从 content_type 推导:', {
    tool_id: tool.tool_id,
    content_type: tool.content_type,
    media_type: tool.media_type
  })

  if (tool.content_type === 'multimodal') {
    switch (tool.media_type) {
      case 'image':
        return 'image'
      case 'audio':
        return 'audio'
      case 'video':
        return 'video'
    }
  }

  // 默认使用 chat 能力
  console.log('[ModelSelector] 默认使用 chat 能力')
  return 'chat'
}

// 加载可用模型列表
async function loadAvailableModels() {
  loading.value = true
  try {
    // 根据当前工具获取需要的能力
    const capability = getRequiredCapability(currentTool.value)

    // 调用 API：第一个参数是 providerCode（留空表示所有供应商），第二个参数是 capability
    const models = await ApiService.getAvailableModels(undefined, capability || undefined)
    availableModels.value = models

    const capabilityMsg = capability ? `（能力: ${capability}）` : ''
    console.log(`[ModelSelector] 已加载模型列表${capabilityMsg}:`, models.length, '个模型')
  } catch (error) {
    console.error('[ModelSelector] 加载模型列表失败:', error)
    availableModels.value = []
  } finally {
    loading.value = false
  }
}

// 切换下拉框
function toggleDropdown() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => {
      const list = selectorRef.value?.querySelector('.model-list')
      const selected = list?.querySelector('.is-selected')
      selected?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    })
  }
}

// 选择模型
function selectModel(modelValue: string) {
  sessionStore.setCurrentModel(modelValue)
  isOpen.value = false
}

// 点击外部关闭下拉框
function handleClickOutside(event: MouseEvent) {
  if (selectorRef.value && !selectorRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

// 监听工具变化，更新默认模型和重新加载模型列表
watch(() => sessionStore.toolId, async (newToolId) => {
  console.log('[ModelSelector] toolId changed:', newToolId)
  if (newToolId) {
    // 从工具列表中获取工具信息
    try {
      const toolsResponse = await ApiService.getTools()
      console.log('[ModelSelector] getTools response categories:', toolsResponse.categories.length)
      let toolFound = false
      for (const category of toolsResponse.categories) {
        const tool = category.tools.find(t => t.tool_id === newToolId)
        if (tool) {
          console.log('[ModelSelector] found tool:', tool)
          currentTool.value = tool
          if (tool.model) {
            defaultModel.value = tool.model
            console.log('[ModelSelector] 工具默认模型:', tool.model)
            // 不再重置手动选择的模型，保留用户的选择
          }
          toolFound = true
          break
        }
      }
      if (!toolFound) {
        console.warn('[ModelSelector] 未找到工具:', newToolId, ', 将加载所有模型')
      }
      // 重新加载模型列表（根据工具能力过滤）
      await loadAvailableModels()
    } catch (error) {
      console.error('[ModelSelector] 获取工具信息失败:', error)
      // 即使获取工具信息失败，也尝试加载所有模型
      await loadAvailableModels()
    }
  } else {
    // 当 toolId 为 null 时，也尝试加载所有模型
    console.log('[ModelSelector] toolId 为空，加载所有模型')
    await loadAvailableModels()
  }
}, { immediate: true })

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.model-selector {
  position: relative;
  display: inline-block;
}

.model-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
  max-width: 300px;
}

.model-button:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

.model-button.is-open {
  background: #f9fafb;
  border-color: #3b82f6;
}

.model-icon {
  width: 1rem;
  height: 1rem;
  color: #6b7280;
  flex-shrink: 0;
}

.model-name {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-icon {
  width: 1rem;
  height: 1rem;
  color: #9ca3af;
  transition: transform 0.2s;
  flex-shrink: 0;
}

.dropdown-icon.is-open {
  transform: rotate(180deg);
}

.model-dropdown {
  position: absolute;
  bottom: calc(100% + 0.5rem); /* 改为向上展开 */
  left: 0;
  min-width: 20rem;
  max-width: 400px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  box-shadow: 0 -10px 15px -3px rgba(0, 0, 0, 0.1); /* 阴影改为向上 */
  z-index: 50;
  max-height: 50vh; /* 限制最大高度为视口的50% */
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.model-list {
  overflow-y: auto;
  flex: 1;
  /* 限制最大高度，确保列表不会超出屏幕 */
  max-height: 50vh;
}

.model-option {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  width: 100%;
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s;
}

.model-option:hover {
  background: #f9fafb;
}

.model-option.is-selected {
  background: #eff6ff;
}

.model-option-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.model-option-name {
  font-weight: 500;
  color: #111827;
  font-size: 0.875rem;
}

.model-option-provider {
  font-size: 0.75rem;
  color: #6b7280;
}

.model-option-description {
  font-size: 0.75rem;
  color: #9ca3af;
  line-height: 1.3;
}

.check-icon {
  width: 1rem;
  height: 1rem;
  color: #3b82f6;
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.loading-state {
  padding: 1rem;
  text-align: center;
  color: #6b7280;
  font-size: 0.875rem;
}

/* 下拉动画（向上展开） */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(0.5rem); /* 改为向上动画 */
}

.dropdown-enter-to,
.dropdown-leave-from {
  opacity: 1;
  transform: translateY(0);
}

/* 响应式设计 */
@media (max-width: 640px) {
  .model-dropdown {
    min-width: 16rem;
    max-width: 90vw;
    left: 50%;
    transform: translateX(-50%);
  }

  .model-list {
    max-height: 40vh;
  }
}
</style>
