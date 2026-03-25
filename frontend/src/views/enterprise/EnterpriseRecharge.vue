<template>
  <div class="enterprise-recharge-page">
    <el-card>
      <template #header>
        <h3>积分充值</h3>
      </template>

      <!-- 充值金额选择 -->
      <div v-if="!currentOrder" class="amount-selection">
        <h4>选择充值金额</h4>

        <!-- 预设金额选项 -->
        <div class="preset-amounts">
          <el-button
            v-for="amount in presetAmounts"
            :key="amount.value"
            :type="selectedAmount === amount.value ? 'primary' : 'default'"
            :size="'large'"
            @click="selectAmount(amount.value)"
            class="amount-btn"
          >
            <div class="amount-content">
              <span class="amount-value">{{ amount.label }}</span>
              <span class="amount-points">送 {{ amount.points }} 积分</span>
            </div>
          </el-button>
        </div>

        <!-- 自定义金额 -->
        <el-divider>或输入自定义金额</el-divider>
        <el-form :model="customForm" label-width="100px" style="max-width: 400px">
          <el-form-item label="充值金额">
            <el-input-number
              v-model="customForm.amount"
              :min="1"
              :max="5000"
              :precision="2"
              :step="1"
              placeholder="请输入充值金额"
              style="width: 200px"
            />
            <span class="unit">元</span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleCustomAmount" :disabled="customForm.amount < 1">
              确认充值
            </el-button>
          </el-form-item>
        </el-form>

        <div class="tips">
          <el-alert type="info" :closable="false">
            <template #title>
              <div>充值说明：</div>
              <ul class="tips-list">
                <li>充值金额范围：1元 - 5000元</li>
                <li>充值比例：1元 = {{ pointsPerYuan }} 积分</li>
                <li>支付方式：扫码支付（支持微信、支付宝等）</li>
                <li>支付成功后积分将自动到账</li>
              </ul>
            </template>
          </el-alert>
        </div>
      </div>

      <!-- 支付二维码 -->
      <div v-else class="payment-qr-code">
        <h4>请扫码支付</h4>

        <div class="qr-container">
          <el-image
            v-if="currentOrder.qr_code_data"
            :src="currentOrder.qr_code_data"
            fit="contain"
            class="qr-image"
          >
            <template #error>
              <div class="image-slot">
                <el-icon><Picture /></el-icon>
                <span>二维码加载失败</span>
              </div>
            </template>
          </el-image>
          <el-skeleton v-else :rows="10" animated />
        </div>

        <div class="order-info">
          <p><strong>订单金额：</strong>¥{{ (currentOrder.amount / 100).toFixed(2) }}</p>
          <p><strong>获得积分：</strong>{{ Math.floor(currentOrder.amount / 100 * pointsPerYuan) }} 积分</p>
          <p><strong>订单号：</strong>{{ currentOrder.out_trade_no }}</p>
          <p><strong>过期时间：</strong>{{ formatExpireTime(currentOrder.expire_at) }}</p>
        </div>

        <div class="status-indicator">
          <el-tag :type="statusTagType" size="large">
            {{ statusText }}
          </el-tag>
          <div v-if="currentOrder.status === 'processing'" class="countdown">
            剩余时间：{{ countdown }}
          </div>
        </div>

        <div class="actions">
          <el-button @click="handleCancelPayment" :disabled="currentOrder.status === 'paid'">
            取消支付
          </el-button>
          <el-button type="primary" @click="refreshStatus" :loading="refreshing">
            刷新状态
          </el-button>
        </div>
      </div>

      <!-- 支付成功 -->
      <el-result
        v-if="paymentSuccess"
        icon="success"
        title="支付成功"
        sub-title="积分已到账，您可以继续使用平台功能"
      >
        <template #extra>
          <el-button type="primary" @click="handleContinue">继续充值</el-button>
          <el-button @click="goToDashboard">返回首页</el-button>
        </template>
      </el-result>

      <!-- 支付失败/超时 -->
      <el-result
        v-if="paymentFailed"
        icon="error"
        :title="paymentFailedTitle"
        :sub-title="paymentFailedMessage"
      >
        <template #extra>
          <el-button type="primary" @click="handleRetry">重新充值</el-button>
          <el-button @click="goToDashboard">返回首页</el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import paymentApi, { type PaymentOrder } from '@/services/paymentApi'
import apiClient from '@/services/apiClient'

const router = useRouter()

// 预设金额选项（元）
const presetAmounts = [
  { value: 1000, label: '10元', points: 1000 },
  { value: 5000, label: '50元', points: 5000 },
  { value: 10000, label: '100元', points: 10000 },
  { value: 20000, label: '200元', points: 20000 },
  { value: 50000, label: '500元', points: 50000 },
  { value: 100000, label: '1000元', points: 100000 }
]

// 积分兑换比例
const pointsPerYuan = ref(100)

// 选中的金额（分）
const selectedAmount = ref<number | null>(null)

// 自定义金额表单
const customForm = ref({
  amount: 1  // 元
})

// 当前订单
const currentOrder = ref<PaymentOrder | null>(null)

// 轮询定时器
let pollingTimer: number | null = null
// 倒计时定时器
let countdownTimer: number | null = null

// 剩余秒数
const remainingSeconds = ref(0)

// 刷新状态中
const refreshing = ref(false)

// 支付成功
const paymentSuccess = ref(false)

// 支付失败
const paymentFailed = ref(false)

const paymentFailedTitle = ref('支付失败')
const paymentFailedMessage = ref('支付过程中出现问题，请重试')

/**
 * 选择预设金额
 */
function selectAmount(amount: number) {
  selectedAmount.value = amount
  createOrder(amount)
}

/**
 * 自定义金额充值
 */
function handleCustomAmount() {
  const amount = Math.round(customForm.value.amount * 100)  // 转换为分
  createOrder(amount)
}

/**
 * 创建支付订单
 */
async function createOrder(amount: number) {
  try {
    const response = await paymentApi.createOrder({ amount })
    currentOrder.value = response.data

    // 计算剩余时间
    if (currentOrder.value.expire_at) {
      const expireTime = new Date(currentOrder.value.expire_at).getTime()
      const now = Date.now()
      remainingSeconds.value = Math.max(0, Math.floor((expireTime - now) / 1000))
    }

    // 开始轮询
    startPolling()
    // 开始倒计时
    startCountdown()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建订单失败')
  }
}

/**
 * 开始轮询订单状态
 */
function startPolling() {
  // 每3秒查询一次
  pollingTimer = window.setInterval(async () => {
    await checkOrderStatus()
  }, 3000)
}

/**
 * 停止轮询
 */
function stopPolling() {
  if (pollingTimer !== null) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
  if (countdownTimer !== null) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

/**
 * 检查订单状态
 */
async function checkOrderStatus() {
  if (!currentOrder.value) return

  try {
    const response = await paymentApi.queryOrder(currentOrder.value.id)
    currentOrder.value = response.data

    // 检查状态
    if (response.data.status === 'paid') {
      handlePaymentSuccess()
    } else if (['failed', 'cancelled', 'timeout'].includes(response.data.status)) {
      handlePaymentFailed(response.data.status)
    }
  } catch (error: any) {
    console.error('查询订单状态失败:', error)
  }
}

/**
 * 开始倒计时
 */
function startCountdown() {
  countdownTimer = window.setInterval(() => {
    if (remainingSeconds.value > 0) {
      remainingSeconds.value--
    } else {
      handlePaymentFailed('timeout')
    }
  }, 1000)
}

/**
 * 倒计时显示
 */
const countdown = computed(() => {
  const minutes = Math.floor(remainingSeconds.value / 60)
  const seconds = remainingSeconds.value % 60
  return `${minutes}分${seconds.toString().padStart(2, '0')}秒`
})

/**
 * 状态标签类型
 */
const statusTagType = computed(() => {
  if (!currentOrder.value) return 'info'
  switch (currentOrder.value.status) {
    case 'paid':
      return 'success'
    case 'processing':
      return 'warning'
    case 'failed':
    case 'cancelled':
    case 'timeout':
      return 'danger'
    default:
      return 'info'
  }
})

/**
 * 状态文本
 */
const statusText = computed(() => {
  if (!currentOrder.value) return ''
  switch (currentOrder.value.status) {
    case 'created':
      return '订单创建中'
    case 'processing':
      return '等待支付'
    case 'paid':
      return '支付成功'
    case 'failed':
      return '支付失败'
    case 'cancelled':
      return '已取消'
    case 'timeout':
      return '订单超时'
    default:
      return '未知状态'
  }
})

/**
 * 处理支付成功
 */
function handlePaymentSuccess() {
  stopPolling()
  paymentSuccess.value = true
  ElMessage.success('支付成功！积分已到账')
}

/**
 * 处理支付失败
 */
function handlePaymentFailed(status: string) {
  stopPolling()
  paymentFailed.value = true

  switch (status) {
    case 'timeout':
      paymentFailedTitle.value = '订单超时'
      paymentFailedMessage.value = '支付时间已超过15分钟，订单已自动取消'
      break
    case 'cancelled':
      paymentFailedTitle.value = '订单已取消'
      paymentFailedMessage.value = '您已取消该订单'
      break
    default:
      paymentFailedTitle.value = '支付失败'
      paymentFailedMessage.value = '支付过程中出现问题，请重试'
  }
}

/**
 * 取消支付
 */
function handleCancelPayment() {
  stopPolling()
  currentOrder.value = null
  selectedAmount.value = null
  paymentFailed.value = false
}

/**
 * 刷新状态
 */
async function refreshStatus() {
  refreshing.value = true
  await checkOrderStatus()
  refreshing.value = false
}

/**
 * 继续充值
 */
function handleContinue() {
  paymentSuccess.value = false
  paymentFailed.value = false
  currentOrder.value = null
  selectedAmount.value = null
}

/**
 * 重新充值
 */
function handleRetry() {
  paymentFailed.value = false
  currentOrder.value = null
  selectedAmount.value = null
}

/**
 * 返回首页
 */
function goToDashboard() {
  router.push('/enterprise/dashboard')
}

/**
 * 格式化过期时间
 */
function formatExpireTime(dateStr?: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 加载积分兑换比例
 */
async function loadPointsPerYuan() {
  try {
    const response = await apiClient.get('/payment/config')
    pointsPerYuan.value = response.data.points_per_yuan || 100
  } catch (error) {
    console.error('加载积分比例失败，使用默认值100')
  }
}

onMounted(() => {
  loadPointsPerYuan()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.enterprise-recharge-page {
  max-width: 800px;
  margin: 0 auto;
}

.amount-selection h4 {
  margin-bottom: 20px;
  color: #303133;
}

.preset-amounts {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.amount-btn {
  height: 80px;
}

.amount-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.amount-value {
  font-size: 18px;
  font-weight: 600;
}

.amount-points {
  font-size: 12px;
  color: #909399;
}

.unit {
  margin-left: 8px;
  color: #606266;
}

.tips {
  margin-top: 24px;
}

.tips-list {
  margin: 8px 0 0 20px;
  color: #606266;
}

.tips-list li {
  margin-bottom: 4px;
}

.payment-qr-code h4 {
  text-align: center;
  margin-bottom: 24px;
  color: #303133;
}

.qr-container {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.qr-image {
  width: 280px;
  height: 280px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
}

.image-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #f5f7fa;
  color: #909399;
}

.image-slot .el-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.order-info {
  text-align: center;
  margin-bottom: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.order-info p {
  margin: 8px 0;
  color: #606266;
}

.status-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.countdown {
  font-size: 14px;
  color: #e6a23c;
  font-weight: 600;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}
</style>
