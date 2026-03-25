<template>
  <div v-if="authStore.isAuthenticated && authStore.user" class="user-info">
    <!-- 积分显示（仅企业用户显示） -->
    <div v-if="authStore.user.enterprise_id" class="points-display">
      <span class="points-icon">💎</span>
      <span class="points-value">{{ formatPoints(userPoints) }}</span>
    </div>
    <div class="user-avatar" @click="toggleDropdown">
      <span class="avatar-text">{{ userInitial }}</span>
    </div>
    <span class="user-name cursor-pointer hover:text-primary-600 transition-colors" @click="toggleDropdown">{{ displayName }}</span>
    
    <!-- 下拉菜单 -->
    <div v-if="showDropdown" class="dropdown-menu">
      <div class="dropdown-item user-info-item">
        <div class="user-info-name">{{ displayName }}</div>
        <div v-if="authStore.user.email" class="user-info-email">{{ authStore.user.email }}</div>
      </div>
      <div class="dropdown-divider"></div>
      <!-- 管理后台入口（仅管理员可见） -->
      <button v-if="authStore.user.is_admin" @click="goToAdmin" class="dropdown-item admin-button">
        管理后台
      </button>
      <!-- 企业后台入口（仅企业管理员可见） -->
      <button v-if="authStore.user.is_enterprise_admin" @click="goToEnterprise" class="dropdown-item enterprise-button">
        {{ enterpriseAdminLabel }}
      </button>
      <div v-if="authStore.user.is_admin || authStore.user.is_enterprise_admin" class="dropdown-divider"></div>
      <button @click="handleLogout" class="dropdown-item logout-button">
        退出
      </button>
    </div>
  </div>
  <div v-else class="user-info">
    <span class="user-name">未登录</span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import apiClient from '@/services/apiClient'

const router = useRouter()
const authStore = useAuthStore()
const showDropdown = ref(false)
const userPoints = ref(0)

// 显示名称：优先使用昵称，如未填写则使用用户名
const displayName = computed(() => {
  if (authStore.user) {
    return authStore.user.nickname || authStore.user.username
  }
  return ''
})

// 企业管理员入口标签：企业名称 + 管理
const enterpriseAdminLabel = computed(() => {
  if (authStore.user?.enterprise_name) {
    return `${authStore.user.enterprise_name}管理`
  }
  return '企业管理'
})

const userInitial = computed(() => {
  if (authStore.user) {
    // 优先使用昵称的首字母，如未填写则使用用户名的首字母
    const name = authStore.user.nickname || authStore.user.username
    if (name) {
      return name.charAt(0).toUpperCase()
    }
  }
  return 'U'
})

// 格式化积分显示
function formatPoints(points: number): string {
  if (points >= 10000) {
    return (points / 10000).toFixed(1) + 'w'
  }
  return points.toString()
}

// 加载用户积分
async function loadUserPoints() {
  if (!authStore.user?.enterprise_id) {
    return
  }

  try {
    const response = await apiClient.get('/enterprise/points/balance')
    userPoints.value = response.data.total_points || 0
  } catch (error) {
    // 静默失败，不影响用户体验
    console.error('加载积分失败:', error)
  }
}

// 切换下拉菜单
function toggleDropdown() {
  showDropdown.value = !showDropdown.value
}

// 点击外部关闭下拉菜单
function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (!target.closest('.user-info')) {
    showDropdown.value = false
  }
}

// 进入管理后台
function goToAdmin() {
  showDropdown.value = false
  router.push('/admin')
}

// 进入企业后台
function goToEnterprise() {
  showDropdown.value = false
  router.push('/enterprise/dashboard')
}

// 登出
function handleLogout() {
  authStore.logout()
  showDropdown.value = false
  router.push('/login')
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  loadUserPoints()
})

// 监听用户登录状态变化，重新加载积分
watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    loadUserPoints()
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.user-info {
  @apply flex items-center gap-3 relative;
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

/* 积分显示 */
.points-display {
  @apply flex items-center gap-1 px-3 py-1 rounded-full bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200;
}

.points-icon {
  font-size: 14px;
}

.points-value {
  @apply text-sm font-semibold text-amber-600;
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

/* 下拉菜单 */
.dropdown-menu {
  @apply absolute top-full right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50;
}

.dropdown-item {
  @apply block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors;
}

.user-info-item {
  @apply cursor-default;
}

.user-info-name {
  @apply font-medium text-gray-900;
}

.user-info-email {
  @apply text-xs text-gray-500 mt-1;
}

.dropdown-divider {
  @apply border-t border-gray-200 my-1;
}

.admin-button {
  @apply text-primary-600 hover:bg-primary-50 cursor-pointer;
}

.enterprise-button {
  @apply text-green-600 hover:bg-green-50 cursor-pointer;
}

.logout-button {
  @apply text-error-600 hover:bg-error-50 cursor-pointer;
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .user-name {
    display: none; /* 移动端只显示头像 */
  }

  .points-display {
    display: none; /* 移动端隐藏积分 */
  }
  
  .user-avatar {
    width: 32px;
    height: 32px;
  }
  
  .avatar-text {
    font-size: 12px;
  }
  
  .dropdown-menu {
    @apply right-0 w-48;
  }
}
</style>

