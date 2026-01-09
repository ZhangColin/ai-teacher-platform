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
      <!-- 页面标题 -->
      <div class="page-header">
        <h1 class="page-title">常用工具</h1>
        <p class="page-description">选择一个工具开始使用</p>
      </div>

      <!-- 按分类显示工具 -->
      <div v-for="category in categories" :key="category.id" class="category-section">
        <!-- 分类标题 -->
        <div class="category-header">
          <div class="category-icon" v-if="category.icon">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getIconPath(category.icon)" />
            </svg>
          </div>
          <h2 class="category-name">{{ category.name }}</h2>
          <span class="category-count">{{ category.tools.length }}</span>
        </div>

        <!-- 工具卡片列表 -->
        <div class="tools-grid">
          <div
            v-for="tool in category.tools"
            :key="tool.id"
            class="tool-card"
            @click="navigateToTool(tool)"
          >
            <!-- 工具图标 -->
            <div class="tool-icon">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getIconPath(tool.icon || 'document-text')" />
              </svg>
            </div>

            <!-- 工具信息 -->
            <div class="tool-info">
              <h3 class="tool-name">{{ tool.name }}</h3>
              <p class="tool-description">{{ tool.description }}</p>
            </div>

            <!-- 工具类型标签 -->
            <div class="tool-badge" :class="tool.type === 'html' ? 'badge-html' : 'badge-builtin'">
              {{ tool.type === 'html' ? 'HTML' : '内置' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="categories.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
        </div>
        <h3 class="empty-title">暂无工具</h3>
        <p class="empty-description">目前还没有可用的工具，请稍后再试</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ApiService } from '../services/apiClient'
import type { ToolCategoryGroup, CommonToolListItem } from '../types'

const router = useRouter()

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

/**
 * 获取图标路径（简化版，实际应该使用图标库）
 */
const getIconPath = (iconName: string): string => {
  const iconPaths: Record<string, string> = {
    'document-text': 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    'chart-bar': 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
    'code': 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
    'template': 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z',
  }
  return iconPaths[iconName] || iconPaths['document-text']
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

/* 工具容器 */
.tools-container {
  @apply px-8 py-6;
  max-width: 1280px;
  margin: 0 auto;
}

/* 页面标题 */
.page-header {
  @apply mb-8;
}

.page-title {
  @apply text-3xl font-bold text-gray-900 mb-2;
}

.page-description {
  @apply text-gray-600;
}

/* 分类区域 */
.category-section {
  @apply mb-10;
}

.category-header {
  @apply flex items-center gap-3 mb-4;
}

.category-icon {
  @apply text-gray-600;
}

.category-name {
  @apply text-xl font-semibold text-gray-900;
}

.category-count {
  @apply text-sm text-gray-500 bg-gray-200 px-2 py-1 rounded-full;
}

/* 工具网格 */
.tools-grid {
  @apply grid gap-4;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}

/* 工具卡片 */
.tool-card {
  @apply relative bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-all cursor-pointer border border-gray-200 hover:border-blue-500;
}

.tool-icon {
  @apply text-blue-600 mb-4;
}

.tool-info {
  @apply mb-4;
}

.tool-name {
  @apply text-lg font-semibold text-gray-900 mb-2;
}

.tool-description {
  @apply text-sm text-gray-600 line-clamp-2;
}

.tool-badge {
  @apply inline-block text-xs px-2 py-1 rounded-full font-medium;
}

.badge-builtin {
  @apply bg-blue-100 text-blue-700;
}

.badge-html {
  @apply bg-purple-100 text-purple-700;
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

/* 响应式 */
@media (max-width: 768px) {
  .tools-container {
    @apply px-4 py-4;
  }

  .page-title {
    @apply text-2xl;
  }

  .tools-grid {
    grid-template-columns: 1fr;
  }

  .category-section {
    @apply mb-6;
  }
}
</style>
