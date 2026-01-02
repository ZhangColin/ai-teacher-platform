<template>
  <div class="ai-tools-layout">
    <!-- 左侧：功能导航栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <SidebarMenu @collapse-change="handleSidebarCollapse" />
    </aside>
    
    <!-- 右侧：聊天区域 -->
    <ChatArea class="chat-area" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import ChatArea from '../components/ChatArea.vue'

const sidebarCollapsed = ref(false)

function handleSidebarCollapse(collapsed: boolean) {
  sidebarCollapsed.value = collapsed
}
</script>

<style scoped>
.ai-tools-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.sidebar {
  width: 240px;
  flex-shrink: 0;
  border-right: 1px solid #e5e7eb;
  background-color: #f9fafb;
  overflow-y: auto;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 0;
  border-right: none;
  overflow: hidden;
}

.chat-area {
  flex: 1;
  min-width: 0;
  background-color: #ffffff;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .sidebar {
    width: 200px;
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

