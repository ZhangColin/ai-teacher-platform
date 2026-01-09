<template>
  <div class="common-tools-view">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p class="loading-text">加载中...</p>
    </div>

    <!-- 错误提示 -->
    <div v-else-if="error" class="error-container">
      <div class="error-icon">
        <svg class="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <h2 class="error-title">加载失败</h2>
      <p class="error-message">{{ error }}</p>
      <button class="retry-button" @click="loadCategories">重试</button>
    </div>

    <!-- 工具卡片 -->
    <div v-else class="tools-container">
      <!-- 按分类显示工具 -->
      <div v-for="category in categories" :key="category.id" class="category-section">
        <!-- 分类标题 - 精简设计 -->
        <div class="category-header">
          <component :is="getIconComponent(category.icon)" class="w-4 h-4 text-gray-500" />
          <span class="category-name">{{ category.name }}</span>
          <div class="category-divider"></div>
        </div>

        <!-- 工具卡片列表 - 网格布局 -->
        <div class="tools-grid">
          <div
            v-for="tool in category.tools"
            :key="tool.id"
            class="tool-card"
            @click="navigateToTool(tool)"
          >
            <!-- 左侧：图标+标题 -->
            <div class="tool-header">
              <div class="tool-icon-wrapper">
                <component :is="getIconComponent(tool.icon)" class="w-6 h-6" />
              </div>
              <h3 class="tool-name">{{ tool.name }}</h3>
            </div>

            <!-- 下方：描述 -->
            <p class="tool-description">{{ tool.description }}</p>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="categories.length === 0" class="empty-state">
        <WrenchIcon class="w-16 h-16 text-gray-300" />
        <h3 class="empty-title">暂无工具</h3>
        <p class="empty-description">目前还没有可用的工具</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  WrenchIcon,
  DocumentTextIcon,
  ChartBarIcon,
  CodeBracketIcon,
  TableCellsIcon,
} from '@heroicons/vue/24/outline'
import { ApiService } from '../services/apiClient'
import type { ToolCategoryGroup, CommonToolListItem } from '../types'

const router = useRouter()

// 图标映射
const iconComponents: Record<string, any> = {
  'document-text': DocumentTextIcon,
  'chart-bar': ChartBarIcon,
  'code-bracket': CodeBracketIcon,
  'table-cells': TableCellsIcon,
  'wrench': WrenchIcon,
}

/**
 * 获取图标组件
 */
function getIconComponent(iconName?: string) {
  if (!iconName) return WrenchIcon
  return iconComponents[iconName] || WrenchIcon
}

// 状态
const loading = ref(true)
const error = ref<string | null>(null)
const categories = ref<ToolCategoryGroup[]>([])

/**
 * 加载工具分类列表
 */
const loadCategories = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await ApiService.getCommonToolCategories()
    categories.value = response.categories
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败，请稍后重试'
    console.error('加载工具分类失败:', err)
  } finally {
    loading.value = false
  }
}

/**
 * 导航到工具页面
 */
const navigateToTool = (tool: CommonToolListItem) => {
  if (tool.type === 'built_in') {
    // 内置工具：导航到对应的路由
    router.push(`/common-tools/${tool.id}`)
  } else if (tool.type === 'html') {
    // HTML工具：导航到HTML工具运行器
    router.push(`/common-tools/html/${tool.id}`)
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.common-tools-view {
  @apply h-full w-full overflow-y-auto;
  background-color: theme('colors.gray.50');
}

/* 加载中 */
.loading-container {
  @apply flex flex-col items-center justify-center h-full gap-4;
}

.spinner {
  @apply w-12 h-12 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin;
}

.loading-text {
  @apply text-gray-600 text-base;
}

/* 错误提示 */
.error-container {
  @apply flex flex-col items-center justify-center h-full gap-4 px-6;
}

.error-icon {
  @apply text-red-500;
}

.error-title {
  @apply text-xl font-semibold text-gray-900;
}

.error-message {
  @apply text-gray-600 text-center;
}

.retry-button {
  @apply mt-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors;
}

/* 工具容器 - 充分利用宽度 */
.tools-container {
  @apply px-8 py-6;
  max-width: 100%;
  margin: 0 auto;
}

/* 分类区域 */
.category-section {
  @apply mb-8;
}

.category-header {
  @apply flex items-center gap-2 mb-3 px-1;
}

.category-name {
  @apply text-xs font-medium text-gray-500 uppercase tracking-wider;
}

.category-divider {
  @apply flex-1 h-px bg-gray-200;
}

/* 工具网格 - 响应式列数 */
.tools-grid {
  @apply grid gap-4;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

/* 工具卡片 */
.tool-card {
  @apply relative bg-white rounded-lg p-5 shadow-sm hover:shadow-md transition-all cursor-pointer border border-gray-200 hover:border-blue-400 hover:bg-blue-50/30 group;
}

/* 卡片头部：图标+标题横向排列 */
.tool-header {
  @apply flex items-center gap-3 mb-3;
}

.tool-icon-wrapper {
  @apply flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100 flex items-center justify-center text-blue-600 group-hover:from-blue-100 group-hover:to-blue-200 transition-all;
}

.tool-name {
  @apply text-base font-semibold text-gray-900;
}

.tool-description {
  @apply text-sm text-gray-600 line-clamp-2;
}

/* 空状态 */
.empty-state {
  @apply flex flex-col items-center justify-center py-16 gap-4;
}

.empty-icon {
  @apply text-gray-400;
}

.empty-title {
  @apply text-xl font-semibold text-gray-900;
}

.empty-description {
  @apply text-gray-600;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .tools-container {
    @apply px-6;
  }
  
  .tools-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
  
  .tool-card {
    @apply p-4;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .tools-container {
    @apply px-4 py-4;
  }

  .tools-grid {
    grid-template-columns: 1fr;
  }

  .category-section {
    @apply mb-6;
  }
  
  .tool-card {
    @apply p-4;
  }
  
  .tool-icon-wrapper {
    @apply w-10 h-10;
  }
  
  .tool-name {
    @apply text-sm;
  }
  
  .tool-description {
    @apply text-sm;
  }
}
</style>
