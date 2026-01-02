<template>
  <div class="ai-tools-layout">
    <!-- 左侧：AI工具选择器 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <AIToolSelector @collapse-change="handleSidebarCollapse" @tool-change="handleToolChange" />
    </aside>
    
    <!-- 右侧：聊天区域 -->
    <ChatArea class="chat-area" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AIToolSelector from '../components/AIToolSelector.vue'
import ChatArea from '../components/ChatArea.vue'

const sidebarCollapsed = ref(false)

function handleSidebarCollapse(collapsed: boolean) {
  sidebarCollapsed.value = collapsed
}

function handleToolChange(toolId: string) {
  // 工具切换逻辑（后续实现）
  console.log('切换到工具:', toolId)
}
</script>

<style scoped>
.ai-tools-layout {
  @apply flex h-full overflow-hidden;
}

.sidebar {
  @apply flex-shrink-0 border-r border-gray-200 overflow-y-auto transition-all duration-300 ease-in-out;
  /* 层级1：容器层 - 浅灰背景，右侧阴影，工具选择器区域 */
  width: 260px; /* 恢复原来的宽度 */
  background-color: theme('colors.gray.50');
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.04);
}

.sidebar.collapsed {
  @apply w-0 border-r-0 overflow-hidden;
}

.chat-area {
  @apply flex-1 min-w-0 bg-white;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .sidebar {
    width: 260px; /* 平板端保持较宽，确保卡片布局舒适 */
  }
  
  .sidebar.collapsed {
    width: 0;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .sidebar {
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    z-index: 40;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .sidebar.open {
    transform: translateX(0);
  }
  
  .sidebar.collapsed {
    width: 240px;
    transform: translateX(-100%);
  }
}
</style>

