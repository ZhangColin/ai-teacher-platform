<template>
  <div class="payment-orders-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>支付订单管理</h3>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filter-bar">
        <el-select
          v-model="filterStatus"
          placeholder="订单状态"
          clearable
          @change="handleFilterChange"
          style="width: 150px"
        >
          <el-option label="已创建" value="created" />
          <el-option label="支付中" value="processing" />
          <el-option label="已支付" value="paid" />
          <el-option label="已失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
          <el-option label="已超时" value="timeout" />
        </el-select>

        <el-input
          v-model="filterOutTradeNo"
          placeholder="商户订单号"
          clearable
          @change="handleFilterChange"
          style="width: 200px"
        />

        <el-input
          v-model="filterThirdTradeNo"
          placeholder="工行流水号"
          clearable
          @change="handleFilterChange"
          style="width: 200px"
        />

        <el-button type="primary" @click="loadOrders">查询</el-button>
        <el-button @click="handleResetFilter">重置</el-button>
      </div>

      <!-- 订单表格 -->
      <el-table
        :data="orders"
        v-loading="loading"
        style="width: 100%; margin-top: 16px"
      >
        <el-table-column prop="out_trade_no" label="商户订单号" width="200" />
        <el-table-column prop="third_trade_no" label="工行流水号" width="180">
          <template #default="{ row }">
            {{ row.third_trade_no || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额（元）" width="100">
          <template #default="{ row }">
            ¥{{ (row.amount / 100).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pay_channel" label="支付渠道" width="120">
          <template #default="{ row }">
            {{ row.pay_channel || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="user_id" label="用户ID" width="180" />
        <el-table-column prop="submitted_at" label="发起时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.submitted_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="paid_at" label="支付时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.paid_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="refunded_amount" label="已退款金额（元）" width="120">
          <template #default="{ row }">
            ¥{{ (row.refunded_amount / 100).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="refund_count" label="退款次数" width="100" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'paid' && row.refunded_amount < row.amount"
              type="warning"
              link
              @click="handleCreateRefund(row)"
            >
              退款
            </el-button>
            <el-button
              v-if="row.refund_count > 0"
              type="info"
              link
              @click="handleViewRefunds(row)"
            >
              查看退款({{ row.refund_count }})
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 订单详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="订单详情"
      width="700px"
    >
      <div v-if="selectedOrder" class="order-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单ID" :span="2">
            {{ selectedOrder.id }}
          </el-descriptions-item>
          <el-descriptions-item label="商户订单号" :span="2">
            {{ selectedOrder.out_trade_no }}
          </el-descriptions-item>
          <el-descriptions-item label="工行流水号" :span="2">
            {{ selectedOrder.third_trade_no || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="金额">
            ¥{{ (selectedOrder.amount / 100).toFixed(2) }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedOrder.status)">
              {{ getStatusText(selectedOrder.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="支付渠道">
            {{ selectedOrder.pay_channel || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="业务类型">
            {{ selectedOrder.business_type || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="用户ID" :span="2">
            {{ selectedOrder.user_id }}
          </el-descriptions-item>
          <el-descriptions-item label="发起时间">
            {{ formatDateTime(selectedOrder.submitted_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="支付时间">
            {{ formatDateTime(selectedOrder.paid_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="超时时间">
            {{ formatDateTime(selectedOrder.expire_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="回调到达时间">
            {{ formatDateTime(selectedOrder.notified_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="回调验签结果" :span="2">
            <el-tag v-if="selectedOrder.notify_verify_result === true" type="success">验签成功</el-tag>
            <el-tag v-else-if="selectedOrder.notify_verify_result === false" type="danger">验签失败</el-tag>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDateTime(selectedOrder.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 工行响应数据 -->
        <div v-if="selectedOrder.icbc_response" class="response-section">
          <h4>工行响应数据</h4>
          <pre class="json-data">{{ JSON.stringify(selectedOrder.icbc_response, null, 2) }}</pre>
        </div>

        <!-- 回调原始数据 -->
        <div v-if="selectedOrder.notify_data" class="response-section">
          <h4>回调原始数据</h4>
          <pre class="json-data">{{ JSON.stringify(selectedOrder.notify_data, null, 2) }}</pre>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 退款记录对话框 -->
    <el-dialog
      v-model="refundListDialogVisible"
      title="退款记录"
      width="800px"
    >
      <el-table
        :data="orderRefunds"
        v-loading="refundListLoading"
        style="width: 100%"
      >
        <el-table-column prop="out_refund_no" label="退款流水号" width="200" />
        <el-table-column prop="refund_amount" label="退款金额（元）" width="100">
          <template #default="{ row }">
            ¥{{ (row.refund_amount / 100).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getRefundStatusType(row.status)">
              {{ getRefundStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="120" />
        <el-table-column prop="refund_reason" label="退款原因" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="refundListDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 发起退款对话框 -->
    <el-dialog
      v-model="createRefundDialogVisible"
      title="发起退款"
      width="500px"
    >
      <div v-if="selectedOrderForRefund">
        <el-descriptions :column="2" border style="margin-bottom: 16px">
          <el-descriptions-item label="商户订单号" :span="2">
            {{ selectedOrderForRefund.out_trade_no }}
          </el-descriptions-item>
          <el-descriptions-item label="订单金额">
            ¥{{ (selectedOrderForRefund.amount / 100).toFixed(2) }}
          </el-descriptions-item>
          <el-descriptions-item label="已退款金额">
            ¥{{ (selectedOrderForRefund.refunded_amount / 100).toFixed(2) }}
          </el-descriptions-item>
          <el-descriptions-item label="可退金额" :span="2">
            ¥{{ ((selectedOrderForRefund.amount - selectedOrderForRefund.refunded_amount) / 100).toFixed(2) }}
          </el-descriptions-item>
        </el-descriptions>

        <el-form :model="refundForm" label-width="120px">
          <el-form-item label="退款金额（元）">
            <el-input-number
              v-model="refundAmountYuan"
              :min="0.01"
              :max="maxRefundAmountYuan"
              :precision="2"
              style="width: 200px"
            />
            <span style="margin-left: 8px; color: #909399;">
              最大可退: ¥{{ maxRefundAmountYuan.toFixed(2) }}
            </span>
          </el-form-item>
          <el-form-item label="退款原因">
            <el-input
              v-model="refundForm.refund_reason"
              type="textarea"
              :rows="3"
              placeholder="请输入退款原因（可选）"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="createRefundDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmRefund" :loading="refunding">
          确认退款
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '@/services/apiClient'
import type { RefundStatus } from '@/types'

// 订单数据
const orders = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 筛选器
const filterStatus = ref<string | undefined>(undefined)
const filterOutTradeNo = ref<string | undefined>(undefined)
const filterThirdTradeNo = ref<string | undefined>(undefined)

// 订单详情对话框
const detailDialogVisible = ref(false)
const selectedOrder = ref<any>(null)

// 退款相关
const refundListDialogVisible = ref(false)
const refundListLoading = ref(false)
const orderRefunds = ref<any[]>([])

const createRefundDialogVisible = ref(false)
const selectedOrderForRefund = ref<any>(null)
const refunding = ref(false)
const refundForm = ref({
  refund_amount: 0,
  refund_reason: ''
})

const refundAmountYuan = computed({
  get: () => refundForm.value.refund_amount / 100,
  set: (val: number) => {
    refundForm.value.refund_amount = Math.round(val * 100)
  }
})

const maxRefundAmountYuan = computed(() => {
  if (!selectedOrderForRefund.value) return 0
  return (selectedOrderForRefund.value.amount - selectedOrderForRefund.value.refunded_amount) / 100
})

/**
 * 获取状态标签类型
 */
function getStatusType(status: string): string {
  switch (status) {
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
}

/**
 * 获取状态文本
 */
function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    created: '已创建',
    processing: '支付中',
    paid: '已支付',
    failed: '已失败',
    cancelled: '已取消',
    timeout: '已超时'
  }
  return statusMap[status] || status
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * 加载订单列表
 */
async function loadOrders() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    if (filterOutTradeNo.value) {
      params.out_trade_no = filterOutTradeNo.value
    }
    if (filterThirdTradeNo.value) {
      params.third_trade_no = filterThirdTradeNo.value
    }

    const response = await apiClient.get('/admin/payment/orders', { params })
    orders.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载订单列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 筛选变化
 */
function handleFilterChange() {
  currentPage.value = 1
  loadOrders()
}

/**
 * 重置筛选
 */
function handleResetFilter() {
  filterStatus.value = undefined
  filterOutTradeNo.value = undefined
  filterThirdTradeNo.value = undefined
  currentPage.value = 1
  loadOrders()
}

/**
 * 页码变化
 */
function handlePageChange() {
  loadOrders()
}

/**
 * 每页数量变化
 */
function handleSizeChange() {
  currentPage.value = 1
  loadOrders()
}

/**
 * 查看详情
 */
function handleViewDetail(row: any) {
  selectedOrder.value = row
  detailDialogVisible.value = true
}

/**
 * 获取退款状态标签类型
 */
function getRefundStatusType(status: string): string {
  const typeMap: Record<string, string> = {
    refund_created: 'info',
    refund_processing: 'warning',
    refund_success: 'success',
    refund_failed: 'danger',
    refund_cancelled: 'info'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取退款状态文本
 */
function getRefundStatusText(status: string): string {
  const textMap: Record<string, string> = {
    refund_created: '已创建',
    refund_processing: '处理中',
    refund_success: '退款成功',
    refund_failed: '退款失败',
    refund_cancelled: '已取消'
  }
  return textMap[status] || status
}

/**
 * 发起退款
 */
function handleCreateRefund(row: any) {
  selectedOrderForRefund.value = row
  refundForm.value = {
    refund_amount: row.amount - row.refunded_amount,  // 默认全额退款剩余部分
    refund_reason: ''
  }
  createRefundDialogVisible.value = true
}

/**
 * 确认退款
 */
async function handleConfirmRefund() {
  if (!selectedOrderForRefund.value) return
  if (refundForm.value.refund_amount <= 0) {
    ElMessage.warning('请输入退款金额')
    return
  }

  refunding.value = true
  try {
    await apiClient.post('/admin/payment/refunds/create', {
      payment_order_id: selectedOrderForRefund.value.id,
      refund_amount: refundForm.value.refund_amount,
      refund_reason: refundForm.value.refund_reason
    })
    ElMessage.success('退款发起成功')
    createRefundDialogVisible.value = false
    loadOrders()  // 刷新订单列表
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '发起退款失败')
  } finally {
    refunding.value = false
  }
}

/**
 * 查看退款记录
 */
async function handleViewRefunds(row: any) {
  refundListLoading.value = true
  refundListDialogVisible.value = true
  try {
    const response = await apiClient.get(`/admin/payment/orders/${row.id}/refunds`)
    orderRefunds.value = response.data.items || []
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取退款记录失败')
  } finally {
    refundListLoading.value = false
  }
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.payment-orders-page {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.order-detail {
  padding: 8px 0;
}

.response-section {
  margin-top: 20px;
}

.response-section h4 {
  margin-bottom: 8px;
  color: #303133;
}

.json-data {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 300px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
