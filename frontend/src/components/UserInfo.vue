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
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.user-avatar:hover {
  transform: scale(1.05);
}

.avatar-text {
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  color: #1f2937;
  font-weight: 500;
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

