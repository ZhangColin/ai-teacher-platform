<template>
  <div class="enterprise-layout">
    <!-- 顶部栏 -->
    <el-header class="enterprise-header">
      <div class="header-left">
        <Logo />
        <span class="enterprise-badge">企业后台</span>
      </div>
      <div class="header-right">
        <el-tag type="success" class="points-badge">
          积分: {{ enterprisePoints?.total_points || 0 }}
        </el-tag>
        <el-divider direction="vertical" />
        <el-button type="primary" link @click="goToHome">返回前台</el-button>
        <el-divider direction="vertical" />
        <span class="user-info">{{ userInfo?.nickname || userInfo?.username }}</span>
        <el-button type="primary" link @click="handleLogout">退出</el-button>
      </div>
    </el-header>

    <el-container class="enterprise-main-container">
      <!-- 侧边栏导航 -->
      <el-aside width="200px" class="enterprise-aside">
        <el-menu
          :default-active="currentRoute"
          class="enterprise-menu"
          router
        >
          <el-menu-item index="/enterprise/dashboard">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据概览</span>
          </el-menu-item>

          <el-menu-item index="/enterprise/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>

          <el-menu-item index="/enterprise/points">
            <el-icon><Coin /></el-icon>
            <span>积分管理</span>
          </el-menu-item>

          <el-menu-item index="/enterprise/consumptions">
            <el-icon><Document /></el-icon>
            <span>消费记录</span>
          </el-menu-item>

          <el-menu-item index="/enterprise/recharge">
            <el-icon><WalletFilled /></el-icon>
            <span>积分充值</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-main class="enterprise-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/authStore'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataAnalysis, User, Coin, Document, WalletFilled } from '@element-plus/icons-vue'
import Logo from '../components/Logo.vue'
import apiClient from '@/services/apiClient'
import type { EnterpriseInfo } from '@/types'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const userInfo = computed(() => authStore.user)
const currentRoute = computed(() => route.path)
const enterprisePoints = ref<EnterpriseInfo | null>(null)

/**
 * 加载企业积分信息
 */
const loadEnterprisePoints = async () => {
  if (!userInfo.value?.enterprise_id) return
  try {
    const response = await apiClient.get(`/enterprise/enterprises/${userInfo.value.enterprise_id}`)
    enterprisePoints.value = response.data
  } catch (error: any) {
    console.error('加载企业积分信息失败:', error)
  }
}

/**
 * 返回前台
 */
const goToHome = () => {
  router.push('/')
}

/**
 * 退出登录
 */
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  loadEnterprisePoints()
})
</script>

<style scoped>
.enterprise-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f0f2f5;
}

/* 顶部栏 */
.enterprise-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background-color: rgba(255, 255, 255, 0.98);
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(12px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.enterprise-badge {
  padding: 4px 12px;
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
  color: white;
  font-size: 13px;
  font-weight: 600;
  border-radius: 4px;
  letter-spacing: 0.5px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right :deep(.el-divider--vertical) {
  height: 1.5em;
  margin: 0;
}

.points-badge {
  font-size: 14px;
  font-weight: 600;
  padding: 6px 12px;
}

.user-info {
  font-size: 14px;
  color: #666;
}

/* 主容器 */
.enterprise-main-container {
  flex: 1;
  overflow: hidden;
}

/* 侧边栏 */
.enterprise-aside {
  background-color: #fff;
  border-right: 1px solid #e8e8e8;
  overflow-y: auto;
}

.enterprise-menu {
  border-right: none;
  height: 100%;
}

/* 主内容区 */
.enterprise-content {
  padding: 24px;
  overflow-y: auto;
  background-color: #f0f2f5;
}
</style>
