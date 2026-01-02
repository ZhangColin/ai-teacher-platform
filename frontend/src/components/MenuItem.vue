<template>
  <div class="menu-item">
    <!-- 一级菜单 -->
    <div
      :class="['menu-item-primary', { active: isActive, 'has-children': hasChildren, 'not-clickable': hasChildren }]"
      @click="handlePrimaryClick"
    >
      <span class="menu-label">{{ item.label }}</span>
      <span v-if="hasChildren" class="menu-arrow">›</span>
    </div>
    
    <!-- 二级菜单 -->
    <div v-if="hasChildren && isExpanded" class="menu-item-children">
      <div
        v-for="child in item.children"
        :key="child.id"
        :class="['menu-item-secondary', { active: activeId === child.id }]"
        @click="handleChildClick(child.id)"
      >
        {{ child.label }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface MenuItemData {
  id: string
  label: string
  children?: MenuItemData[]
}

const props = defineProps<{
  item: MenuItemData
  activeId: string | null
}>()

const emit = defineEmits<{
  click: [id: string]
}>()

const isExpanded = ref(true) // 当前迭代固定展开

const hasChildren = computed(() => props.item.children && props.item.children.length > 0)
const isActive = computed(() => {
  if (hasChildren.value) {
    return false // 有二级菜单时，一级菜单不显示激活状态
  }
  return props.activeId === props.item.id
})

function handlePrimaryClick() {
  if (!hasChildren.value) {
    emit('click', props.item.id)
  }
}

function handleChildClick(childId: string) {
  emit('click', childId)
}
</script>

<style scoped>
.menu-item {
  margin-bottom: 2px;
}

.menu-item-primary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #374151;
  font-size: 14px;
}

.menu-item-primary:hover:not(.not-clickable) {
  background-color: #f3f4f6;
}

.menu-item-primary.not-clickable {
  cursor: default;
  color: #4b5563;
  font-weight: 600;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.menu-item-primary.active {
  background-color: #eff6ff;
  color: #2563eb;
  font-weight: 600;
}

.menu-label {
  flex: 1;
}

.menu-arrow {
  color: #9ca3af;
  font-size: 16px;
  margin-left: 8px;
  transition: transform 0.2s;
}

.menu-item-children {
  margin-left: 20px;
  margin-top: 4px;
  padding-left: 8px;
  border-left: 2px solid #e5e7eb;
}

.menu-item-secondary {
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  color: #6b7280;
  font-size: 13px;
}

.menu-item-secondary:hover {
  background-color: #f3f4f6;
  color: #1f2937;
}

.menu-item-secondary.active {
  background-color: #eff6ff;
  color: #2563eb;
  font-weight: 600;
}
</style>

