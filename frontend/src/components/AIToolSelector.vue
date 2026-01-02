<template>
  <div class="tool-selector" :class="{ collapsed: isCollapsed }">
    <div v-if="!isCollapsed" class="tool-selector-content">
      <!-- 工具列表 -->
      <div class="tool-list">
        <!-- 所有工具都按分类组织 -->
        <div
          v-for="category in tools"
          :key="category.id"
          class="tool-category"
        >
          <div class="category-header">
            <div class="category-icon">
              <component :is="category.icon" class="w-5 h-5" />
            </div>
            <span class="category-name">{{ category.label }}</span>
          </div>
          <div class="category-tools">
            <div
              v-for="tool in category.children || []"
              :key="tool.id"
              :class="['tool-card', { active: activeToolId === tool.id }]"
              @click="handleToolClick(tool.id)"
            >
              <div class="tool-icon">
                <component :is="tool.icon" class="w-5 h-5" />
              </div>
              <div class="tool-info">
                <div class="tool-name">{{ tool.label }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  DocumentTextIcon,
  PhotoIcon,
  VideoCameraIcon,
  SparklesIcon,
  CommandLineIcon,
  BeakerIcon,
} from '@heroicons/vue/24/outline'

interface ToolItem {
  id: string
  label: string
  description?: string
  icon: any
  children?: ToolItem[]
}

const props = defineProps<{
  collapsed?: boolean
}>()

const emit = defineEmits<{
  'tool-change': [toolId: string]
  'collapse-change': [collapsed: boolean]
}>()

// 工具数据（写死，后续从API获取）- 所有工具都按分类组织
const tools: ToolItem[] = [
  {
    id: 'content-gen',
    label: '内容生成',
    icon: SparklesIcon,
    children: [
      {
        id: 'text-gen',
        label: '文生文',
        icon: DocumentTextIcon,
      },
      {
        id: 'image-gen',
        label: '文生图',
        icon: PhotoIcon,
      },
      {
        id: 'video-gen',
        label: '文生视频',
        icon: VideoCameraIcon,
      },
    ],
  },
  {
    id: 'agents',
    label: '智能体',
    icon: SparklesIcon,
    children: [
      {
        id: 'prompt-wizard',
        label: '提示词向导',
        icon: CommandLineIcon,
      },
      {
        id: 'lyar',
        label: 'Lyar',
        icon: BeakerIcon,
      },
    ],
  },
]

const activeToolId = ref<string | null>('prompt-wizard')
const isCollapsed = ref(props.collapsed ?? false)

// 同步外部传入的 collapsed 状态
watch(() => props.collapsed, (newVal) => {
  if (newVal !== undefined) {
    isCollapsed.value = newVal
  }
})

function handleToolClick(toolId: string) {
  activeToolId.value = toolId
  emit('tool-change', toolId)
}

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
  emit('collapse-change', isCollapsed.value)
}
</script>

<style scoped>
.tool-selector {
  height: 100%;
  position: relative;
  transition: width 0.3s;
}

.tool-selector.collapsed {
  width: 0;
  overflow: visible; /* 允许按钮显示在容器外 */
}

.tool-selector-content {
  padding: 20px 16px;
  height: 100%;
  overflow-y: auto;
}

.tool-list {
  @apply flex flex-col gap-4;
}

/* 工具分类 */

/* 工具分类 */
.tool-category {
  @apply mb-1;
}

.category-header {
  @apply flex items-center gap-2 px-2 py-2 mb-2;
}

.category-icon {
  @apply w-5 h-5 text-gray-500;
}

.category-name {
  @apply text-sm font-semibold text-gray-700;
}

.category-tools {
  @apply flex flex-col gap-2 pl-7;
}

/* 工具卡片（缩小版） */
.tool-card {
  @apply flex items-center gap-2.5 px-3 py-2.5 rounded-lg cursor-pointer transition-all duration-200;
  background-color: theme('colors.white');
  border: 1px solid theme('colors.gray.200');
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.tool-card:hover {
  border-color: theme('colors.primary.300');
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.tool-card.active {
  border-color: theme('colors.primary.500');
  background-color: theme('colors.primary.50');
  box-shadow: 0 2px 4px theme('colors.primary.500 / 0.15');
}

.tool-icon {
  @apply flex-shrink-0 w-8 h-8 rounded-md flex items-center justify-center;
  background-color: theme('colors.gray.100');
  color: theme('colors.gray.600');
  transition: all 0.2s;
}

.tool-card:hover .tool-icon {
  background-color: theme('colors.primary.100');
  color: theme('colors.primary.600');
}

.tool-card.active .tool-icon {
  background-color: theme('colors.primary.500');
  color: theme('colors.white');
}

.tool-info {
  @apply flex-1 min-w-0;
}

.tool-name {
  @apply text-sm font-medium text-gray-900;
}

.tool-card.active .tool-name {
  @apply text-primary-700;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .tool-selector-content {
    padding: 16px 12px;
  }
  
  .category-name {
    font-size: 13px;
  }
  
  .tool-card {
    padding: 10px 12px;
  }
  
  .tool-icon {
    width: 32px;
    height: 32px;
  }
  
  .tool-name {
    font-size: 13px;
  }
}

/* 移动端响应式 */
@media (max-width: 767px) {
  .tool-selector-content {
    padding: 16px 12px;
  }
}
</style>

