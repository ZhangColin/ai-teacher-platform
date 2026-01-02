<template>
  <div class="sidebar-menu" :class="{ collapsed: isCollapsed }">
    <div v-if="!isCollapsed" class="menu-list">
      <MenuItem
        v-for="item in menuItems"
        :key="item.id"
        :item="item"
        :active-id="activeMenuItemId"
        @click="handleMenuItemClick"
      />
    </div>
    <button class="collapse-button" @click="toggleCollapse">
      {{ isCollapsed ? '›' : '‹' }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MenuItem from './MenuItem.vue'

const emit = defineEmits<{
  'collapse-change': [collapsed: boolean]
}>()

// 写死的菜单数据
const menuItems = [
  { id: 'text-gen', label: '文生文' },
  { id: 'image-gen', label: '文生图' },
  { id: 'video-gen', label: '文生视频' },
  {
    id: 'agents',
    label: '智能体',
    children: [
      { id: 'prompt-wizard', label: '提示词向导' },
      { id: 'lyar', label: 'Lyar' },
    ],
  },
]

const activeMenuItemId = ref<string | null>('prompt-wizard')
const isCollapsed = ref(false)

function handleMenuItemClick(itemId: string) {
  activeMenuItemId.value = itemId
}

function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
  emit('collapse-change', isCollapsed.value)
}
</script>

<style scoped>
.sidebar-menu {
  height: 100%;
  position: relative;
  transition: width 0.3s;
}

.sidebar-menu.collapsed {
  width: 0;
  overflow: hidden;
}

.menu-list {
  padding: 8px;
  height: 100%;
  overflow-y: auto;
}

.collapse-button {
  position: absolute;
  top: 12px;
  right: -16px;
  width: 32px;
  height: 32px;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #6b7280;
  z-index: 10;
  transition: all 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.collapse-button:hover {
  background-color: #f3f4f6;
  color: #1f2937;
}
</style>

