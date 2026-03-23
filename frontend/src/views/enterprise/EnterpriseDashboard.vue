<template>
  <div class="enterprise-dashboard">
    <!-- 企业信息头部 -->
    <el-card class="header-card">
      <div class="enterprise-info">
        <div class="info-item">
          <span class="label">企业名称:</span>
          <span class="value">{{ enterpriseInfo?.name || '-' }}</span>
        </div>
        <el-divider direction="vertical" />
        <div class="info-item">
          <span class="label">状态:</span>
          <el-tag :type="getStatusType(enterpriseInfo?.status)" size="small">
            {{ getStatusLabel(enterpriseInfo?.status) }}
          </el-tag>
        </div>
        <el-divider direction="vertical" />
        <div class="info-item">
          <span class="label">用户数:</span>
          <span class="value">{{ userCount }}</span>
        </div>
      </div>
    </el-card>

    <!-- 积分概览卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card total-points">
          <div class="stat-content">
            <div class="stat-value">{{ enterpriseInfo?.total_points || 0 }}</div>
            <div class="stat-label">总积分</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card paid-points">
          <div class="stat-content">
            <div class="stat-value">{{ enterpriseInfo?.balance_paid || 0 }}</div>
            <div class="stat-label">充值积分</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card gratis-points">
          <div class="stat-content">
            <div class="stat-value">{{ enterpriseInfo?.balance_gratis || 0 }}</div>
            <div class="stat-label">赠送积分</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作按钮区域 -->
    <el-card class="action-card">
      <div class="action-buttons">
        <el-button type="primary" size="large" @click="showRechargeDialog = true">
          <el-icon><Wallet /></el-icon>
          <span>在线充值</span>
        </el-button>
        <el-button size="large" @click="goToTransactions">
          <el-icon><Document /></el-icon>
          <span>充值记录</span>
        </el-button>
        <el-button size="large" @click="goToConsumptions">
          <el-icon><DataLine /></el-icon>
          <span>消费记录</span>
        </el-button>
      </div>
    </el-card>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span class="chart-title">本月消耗趋势</span>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span class="chart-title">模型使用分布</span>
          </template>
          <div ref="modelChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 用户排行 -->
    <el-card class="ranking-card">
      <template #header>
        <div class="card-header">
          <span>用户消耗排名 Top 10</span>
          <el-button type="primary" link @click="goToUsers">查看全部</el-button>
        </div>
      </template>
      <el-table :data="topUsers" v-loading="loadingUsers" stripe>
        <el-table-column type="index" label="排名" width="60" />
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

    <!-- 充值二维码弹窗 -->
    <el-dialog
      v-model="showRechargeDialog"
      title="在线充值"
      width="400px"
      center
    >
      <div class="recharge-dialog">
        <div class="recharge-amount-selector">
          <span class="amount-label">选择充值金额:</span>
          <div class="amount-options">
            <div
              v-for="option in amountOptions"
              :key="option.points"
              :class="['amount-option', { active: selectedAmount === option.points }]"
              @click="selectedAmount = option.points"
            >
              <div class="amount-points">{{ option.points }}积分</div>
              <div class="amount-price">¥{{ option.price }}</div>
            </div>
          </div>
        </div>

        <div class="qrcode-container">
          <div class="qrcode-placeholder">
            <div class="qrcode-icon">
              <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="10" y="10" width="30" height="30" fill="#333"/>
                <rect x="60" y="10" width="30" height="30" fill="#333"/>
                <rect x="10" y="60" width="30" height="30" fill="#333"/>
                <rect x="50" y="50" width="10" height="10" fill="#333"/>
                <rect x="70" y="70" width="10" height="10" fill="#333"/>
                <rect x="80" y="60" width="10" height="10" fill="#333"/>
                <rect x="60" y="80" width="10" height="10" fill="#333"/>
              </svg>
            </div>
            <p class="qrcode-hint">请使用微信/支付宝扫码支付</p>
            <p class="qrcode-amount">应付金额: ¥{{ selectedAmountPrice }}</p>
          </div>
        </div>

        <div class="recharge-tips">
          <el-icon color="#E6A23C"><Warning /></el-icon>
          <span>支付功能开发中，此为演示页面</span>
        </div>
      </div>

      <template #footer>
        <el-button @click="showRechargeDialog = false">取消</el-button>
        <el-button type="primary" @click="handleRecharge">确认充值</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { ElMessage } from 'element-plus'
import { Wallet, Document, DataLine, Warning } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import apiClient from '@/services/apiClient'
import type { EnterpriseInfo } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

const userInfo = computed(() => authStore.user)
const enterpriseInfo = ref<EnterpriseInfo | null>(null)
const userCount = ref(0)
const topUsers = ref<any[]>([])
const loadingUsers = ref(false)
const showRechargeDialog = ref(false)

// 图表引用
const trendChartRef = ref<HTMLElement>()
const modelChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let modelChart: echarts.ECharts | null = null

// 充值金额选项
interface AmountOption {
  points: number
  price: number
}

const amountOptions: AmountOption[] = [
  { points: 100, price: 10 },
  { points: 500, price: 45 },
  { points: 1000, price: 85 },
  { points: 5000, price: 380 },
  { points: 10000, price: 700 },
  { points: 50000, price: 3000 }
]
const selectedAmount = ref(100)

const selectedAmountPrice = computed(() => {
  const option = amountOptions.find(o => o.points === selectedAmount.value)
  return option?.price || 0
})

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
        page_size: 10,
        sort_by: 'total_consumed',
        sort_order: 'desc'
      }
    })
    topUsers.value = response.data.users || []
    userCount.value = response.data.total || 0
  } catch (error: any) {
    console.error('加载用户排行失败:', error)
  } finally {
    loadingUsers.value = false
  }
}

/**
 * 加载消费统计数据
 */
const loadConsumptionStats = async () => {
  if (!userInfo.value?.enterprise_id) return

  try {
    const response = await apiClient.get('/enterprise/consumptions/stats', {
      params: { days: 30 }
    })

    const stats = response.data
    initCharts(stats.trend || [], stats.model_distribution || [])
  } catch (error: any) {
    console.error('加载统计数据失败:', error)
    // 失败时使用空数据初始化图表
    initCharts([], [])
  }
}

/**
 * 初始化图表
 */
const initCharts = (trendData: any[] = [], modelData: any[] = []) => {
  initTrendChart(trendData)
  initModelChart(modelData)
}

/**
 * 初始化趋势图
 */
const initTrendChart = (trendData: any[] = []) => {
  if (!trendChartRef.value) return

  trendChart = echarts.init(trendChartRef.value)

  // 如果有数据，使用真实数据；否则显示空图表
  const dates: string[] = []
  const data: number[] = []

  if (trendData.length > 0) {
    // 填充真实数据
    trendData.forEach(item => {
      const date = new Date(item.date)
      dates.push(`${date.getMonth() + 1}/${date.getDate()}`)
      data.push(item.points)
    })
  }

  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value',
      name: '积分'
    },
    series: [{
      name: '消耗积分',
      type: 'line',
      smooth: true,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
        ])
      },
      lineStyle: {
        color: '#409EFF',
        width: 2
      },
      itemStyle: {
        color: '#409EFF'
      },
      data: data
    }]
  }

  trendChart.setOption(option)
}

/**
 * 初始化模型分布图
 */
const initModelChart = (modelData: any[] = []) => {
  if (!modelChartRef.value) return

  modelChart = echarts.init(modelChartRef.value)

  // 颜色配置
  const colors = ['#67C23A', '#409EFF', '#E6A23C', '#F56C6C', '#909399']

  // 如果有数据，使用真实数据；否则显示空图表
  const data = modelData.length > 0
    ? modelData.map((item, index) => ({
        value: item.value || item.points,
        name: item.name,
        itemStyle: { color: colors[index % colors.length] }
      }))
    : []

  const option: EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}积分 ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: '10%',
      top: 'center'
    },
    series: [{
      name: '模型使用',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 20,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: data
    }]
  }

  modelChart.setOption(option)
}

/**
 * 窗口大小改变时重绘图表
 */
const handleResize = () => {
  trendChart?.resize()
  modelChart?.resize()
}

/**
 * 获取状态类型
 */
const getStatusType = (status?: string) => {
  switch (status) {
    case 'active': return 'success'
    case 'suspended': return 'warning'
    case 'archived': return 'danger'
    default: return 'info'
  }
}

/**
 * 获取状态标签
 */
const getStatusLabel = (status?: string) => {
  switch (status) {
    case 'active': return '正常'
    case 'suspended': return '暂停'
    case 'archived': return '归档'
    default: return status || '-'
  }
}

/**
 * 跳转到用户管理
 */
const goToUsers = () => {
  router.push('/enterprise/users')
}

/**
 * 跳转到充值记录
 */
const goToTransactions = () => {
  router.push('/enterprise/points')
}

/**
 * 跳转到消费记录
 */
const goToConsumptions = () => {
  router.push('/enterprise/consumptions')
}

/**
 * 处理充值
 */
const handleRecharge = () => {
  ElMessage.info('支付功能开发中，请联系管理员进行充值')
  showRechargeDialog.value = false
}

onMounted(async () => {
  await loadEnterpriseInfo()
  await loadTopUsers()
  await loadConsumptionStats()

  await nextTick()
  initCharts()

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  trendChart?.dispose()
  modelChart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.enterprise-dashboard {
  padding: 20px;
}

/* 企业信息头部 */
.header-card {
  margin-bottom: 20px;
}

.enterprise-info {
  display: flex;
  align-items: center;
  gap: 24px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item .label {
  color: #909399;
  font-size: 14px;
}

.info-item .value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

/* 积分概览卡片 */
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
  padding: 20px 0;
  text-align: center;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.total-points .stat-value {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.paid-points .stat-value {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.gratis-points .stat-value {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 操作按钮区域 */
.action-card {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.action-buttons .el-button {
  min-width: 140px;
}

.action-buttons .el-button .el-icon {
  margin-right: 6px;
}

/* 图表区域 */
.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 360px;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.chart-container {
  width: 100%;
  height: 280px;
}

/* 用户排行 */
.ranking-card {
  margin-bottom: 20px;
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

/* 充值弹窗 */
.recharge-dialog {
  padding: 20px 0;
}

.recharge-amount-selector {
  margin-bottom: 24px;
}

.amount-label {
  display: block;
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
}

.amount-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.amount-option {
  border: 1px solid #DCDFE6;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.amount-option:hover {
  border-color: #409EFF;
  background-color: #F0F7FF;
}

.amount-option.active {
  border-color: #409EFF;
  background-color: #E6F1FC;
}

.amount-points {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.amount-price {
  font-size: 14px;
  color: #F56C6C;
  margin-top: 4px;
}

.qrcode-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
  border-top: 1px solid #EBEEF5;
  border-bottom: 1px solid #EBEEF5;
  margin-bottom: 16px;
}

.qrcode-placeholder {
  text-align: center;
}

.qrcode-icon {
  width: 120px;
  height: 120px;
  margin: 0 auto;
  padding: 10px;
  background-color: #fff;
  border-radius: 8px;
}

.qrcode-icon svg {
  width: 100%;
  height: 100%;
}

.qrcode-hint {
  margin: 16px 0 8px;
  font-size: 14px;
  color: #606266;
}

.qrcode-amount {
  font-size: 18px;
  font-weight: 600;
  color: #F56C6C;
}

.recharge-tips {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background-color: #FDF6EC;
  border-radius: 4px;
  font-size: 13px;
  color: #E6A23C;
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-row .el-col {
    margin-bottom: 12px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .el-button {
    width: 100%;
  }

  .amount-options {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
