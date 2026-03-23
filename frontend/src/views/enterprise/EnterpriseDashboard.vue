<template>
  <div class="enterprise-dashboard">
    <!-- 欢迎卡片 -->
    <el-card class="welcome-card">
      <h2>欢迎使用企业后台，{{ userInfo?.nickname || userInfo?.username }}！</h2>
      <p class="subtitle">管理您的企业用户、积分和消费记录</p>
    </el-card>

    <!-- 积分概览卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card total-points">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="32"><Coin /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ enterpriseInfo?.total_points || 0 }}</div>
              <div class="stat-label">总积分</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card gratis-points">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="32"><Present /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ enterpriseInfo?.balance_gratis || 0 }}</div>
              <div class="stat-label">赠送积分</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card paid-points">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="32"><Wallet /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ enterpriseInfo?.balance_paid || 0 }}</div>
              <div class="stat-label">充值积分</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card debt-points">
          <div class="stat-content">
            <div class="stat-icon">
              <el-icon :size="32"><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ enterpriseInfo?.debt_points || 0 }}</div>
              <div class="stat-label">负债积分</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 用户和消费统计 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>用户排行</span>
              <el-button type="primary" link @click="goToUsers">查看全部</el-button>
            </div>
          </template>
          <el-table :data="topUsers" v-loading="loadingUsers" stripe>
            <el-table-column prop="username" label="用户名" width="120" />
            <el-table-column prop="nickname" label="昵称" width="120" />
            <el-table-column label="总消耗" width="100">
              <template #default="{ row }">
                <span class="points-consumed">{{ row.total_consumed || 0 }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                  {{ row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>最近消费</span>
              <el-button type="primary" link @click="goToConsumptions">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentConsumptions" v-loading="loadingConsumptions" stripe>
            <el-table-column label="时间" width="140">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="username" label="用户" width="100" />
            <el-table-column label="消耗积分" width="80">
              <template #default="{ row }">
                <span class="points-deducted">-{{ row.points }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="model_name" label="模型" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { ElMessage } from 'element-plus'
import { Coin, Present, Wallet, Warning } from '@element-plus/icons-vue'
import apiClient from '@/services/apiClient'
import type { EnterpriseInfo } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

const userInfo = computed(() => authStore.user)
const enterpriseInfo = ref<EnterpriseInfo | null>(null)
const topUsers = ref<any[]>([])
const recentConsumptions = ref<any[]>([])
const loadingUsers = ref(false)
const loadingConsumptions = ref(false)

/**
 * 加载企业信息
 */
const loadEnterpriseInfo = async () => {
  if (!userInfo.value?.enterprise_id) return
  try {
    const response = await apiClient.get(`/enterprise/enterprises/${userInfo.value.enterprise_id}`)
    enterpriseInfo.value = response.data
  } catch (error: any) {
    console.error('加载企业信息失败:', error)
  }
}

/**
 * 加载用户排行
 */
const loadTopUsers = async () => {
  if (!userInfo.value?.enterprise_id) return
  loadingUsers.value = true
  try {
    const response = await apiClient.get('/enterprise/users', {
      params: {
        page: 1,
        page_size: 5,
        sort_by: 'total_consumed',
        sort_order: 'desc'
      }
    })
    topUsers.value = response.data.items
  } catch (error: any) {
    console.error('加载用户排行失败:', error)
  } finally {
    loadingUsers.value = false
  }
}

/**
 * 加载最近消费
 */
const loadRecentConsumptions = async () => {
  if (!userInfo.value?.enterprise_id) return
  loadingConsumptions.value = true
  try {
    const response = await apiClient.get('/enterprise/consumptions', {
      params: {
        page: 1,
        page_size: 5
      }
    })
    recentConsumptions.value = response.data.items
  } catch (error: any) {
    console.error('加载消费记录失败:', error)
  } finally {
    loadingConsumptions.value = false
  }
}

/**
 * 跳转到用户管理
 */
const goToUsers = () => {
  router.push('/enterprise/users')
}

/**
 * 跳转到消费记录
 */
const goToConsumptions = () => {
  router.push('/enterprise/consumptions')
}

/**
 * 格式化日期时间
 */
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-'
  const date = new Date(dateTime)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))

  if (hours < 1) {
    const minutes = Math.floor(diff / (1000 * 60))
    return minutes < 1 ? '刚刚' : `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else if (hours < 24 * 7) {
    const days = Math.floor(hours / 24)
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

onMounted(() => {
  loadEnterpriseInfo()
  loadTopUsers()
  loadRecentConsumptions()
})
</script>

<style scoped>
.enterprise-dashboard {
  padding: 20px;
}

.welcome-card {
  margin-bottom: 20px;
}

.welcome-card h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 8px;
}

.total-points .stat-icon {
  background-color: #ecf5ff;
  color: #409eff;
}

.gratis-points .stat-icon {
  background-color: #f0f9ff;
  color: #67c23a;
}

.paid-points .stat-icon {
  background-color: #fdf6ec;
  color: #e6a23c;
}

.debt-points .stat-icon {
  background-color: #fef0f0;
  color: #f56c6c;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.chart-card {
  height: 380px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.points-consumed {
  color: #f56c6c;
  font-weight: 600;
}

.points-deducted {
  color: #f56c6c;
  font-weight: 600;
}
</style>
