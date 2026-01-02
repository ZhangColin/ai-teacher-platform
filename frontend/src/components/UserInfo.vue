<template>
  <div class="user-info">
    <div class="user-avatar">
      <span class="avatar-text">{{ userInitial }}</span>
    </div>
    <span class="user-name">{{ user.name }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// 写死的用户数据
const user = {
  name: '用户',
  avatar: '', // 当前不使用头像URL
}

const userInitial = computed(() => user.name.charAt(0))
</script>

<style scoped>
.user-info {
  @apply flex items-center gap-3;
}

.user-avatar {
  @apply w-9 h-9 rounded-full flex items-center justify-center cursor-pointer transition-transform duration-200;
  /* 使用主色渐变（待品牌色提取后更新） */
  background: linear-gradient(135deg, theme('colors.primary.500') 0%, theme('colors.primary.700') 100%);
  box-shadow: 0 2px 4px theme('colors.primary.500 / 0.3');
}

.user-avatar:hover {
  @apply scale-105;
  box-shadow: 0 4px 8px theme('colors.primary.500 / 0.4');
}

.avatar-text {
  @apply text-white text-sm font-semibold;
}

.user-name {
  @apply text-sm text-gray-900 font-medium;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .user-info {
    gap: 10px;
  }
  
  .user-avatar {
    width: 34px;
    height: 34px;
  }
  
  .avatar-text {
    font-size: 13px;
  }
  
  .user-name {
    font-size: 13px;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .user-name {
    display: none; /* 移动端只显示头像 */
  }
  
  .user-avatar {
    width: 32px;
    height: 32px;
  }
  
  .avatar-text {
    font-size: 12px;
  }
}
</style>

