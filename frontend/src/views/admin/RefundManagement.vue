<template>
  <div class="refund-management-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>退款管理</h3>
          <el-button type="primary" @click="showCreateDialog = true">
            发起退款
          </el-button>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filter-bar">
        <el-select
          v-model="filterStatus"
          placeholder="退款状态"
          clearable
          @change="handleFilterChange"
          style="width: 150px"
        >
          <el-option label="已创建" value="refund_created" />
          <el-option label="处理中" value="refund_processing" />
          <el-option label="退款成功" value="refund_success" />
          <el-option label="退款失败" value="refund_failed" />
          <el-option label="已取消" value="refund_cancelled" />
        </el-select>

        <el-input
          v-model="filterOutTradeNo"
          placeholder="商户订单号"
          clearable
          @change="handleFilterChange"
          style="width: 200px"
        />

        <el-input
          v-model="filterOutRefundNo"
          placeholder="退款流水号"
          clearable
          @change="handleFilterChange"
          style="width: 200px"
        />

        <el-button type="primary" @click="loadRefunds">查询</el-button>
        <el-button @click="handleResetFilter">重置</el-button>
      </div>

      <!-- 退款表格 -->
      <el-table
        :data="refunds"
        v-loading="loading"
        style="width: 100%; margin-top: 16px"
      >
        <el-table-column prop="out_refund_no" label="退款流水号" width="200" />
        <el-table-column prop="payment_order_out_trade_no" label="商户订单号" width="200">
          <template #default="{ row }">
            {{ row.payment_order_out_trade_no || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="refund_amount" label="退款金额（元）" width="120">
          <template #default="{ row }">
            ¥{{ (row.refund_amount / 100).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="real_refund_amount" label="实际退款（元）" width="120">
          <template #default="{ row }">
            {{ row.real_refund_amount ? '¥' + (row.real_refund_amount / 100).toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              v-if="row.status === 'refund_processing'"
              type="warning"
              link
              :loading="refreshingId === row.id"
              @click="handleQueryStatus(row)"
            >
              {{ refreshingId === row.id ? '查询中...' : '查询状态' }}
            </el-button>
            <span v-if="row.status === 'refund_success'" class="text-success">
              已完成
            </span>
            <span v-if="row.status === 'refund_failed'" class="text-failed">
              失败
            </span>
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

    <!-- 发起退款对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="发起退款"
      width="500px"
    >
      <el-form :model="createForm" label-width="120px">
        <el-form-item label="支付订单ID">
          <el-input
            v-model="createForm.payment_order_id"
            placeholder="请输入支付订单ID"
          />
        </el-form-item>
        <el-form-item label="退款金额（元）">
          <el-input-number
            v-model="refundAmountYuan"
            :min="0.01"
            :precision="2"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="退款原因">
          <el-input
            v-model="createForm.refund_reason"
            type="textarea"
            :rows="3"
            placeholder="请输入退款原因（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateRefund" :loading="creating">
          确认退款
        </el-button>
      </template>
    </el-dialog>

    <!-- 退款详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="退款详情"
      width="700px"
    >
      <div v-if="selectedRefund" class="refund-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="退款ID" :span="2">
            {{ selectedRefund.id }}
          </el-descriptions-item>
          <el-descriptions-item label="退款流水号" :span="2">
            {{ selectedRefund.out_refund_no }}
          </el-descriptions-item>
          <el-descriptions-item label="商户订单号" :span="2">
            {{ selectedRefund.payment_order_out_trade_no || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="退款金额">
            ¥{{ (selectedRefund.refund_amount / 100).toFixed(2) }}
          </el-descriptions-item>
          <el-descriptions-item label="实际退款金额">
            {{ selectedRefund.real_refund_amount ? '¥' + (selectedRefund.real_refund_amount / 100).toFixed(2) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedRefund.status)">
              {{ getStatusText(selectedRefund.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="工行流水号">
            {{ selectedRefund.third_refund_no || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="操作人" :span="2">
            {{ selectedRefund.operator_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="退款原因" :span="2">
            {{ selectedRefund.refund_reason || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="发起时间">
            {{ formatDateTime(selectedRefund.submitted_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="成功时间">
            {{ formatDateTime(selectedRefund.success_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDateTime(selectedRefund.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 工行响应数据 -->
        <div v-if="selectedRefund.icbc_refund_response" class="response-section">
          <h4>工行响应数据</h4>
          <pre class="json-data">{{ JSON.stringify(selectedRefund.icbc_refund_response, null, 2) }}</pre>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button
          v-if="selectedRefund?.status === 'refund_processing'"
          type="warning"
          :loading="refreshingId === selectedRefund.id"
          @click="handleQueryStatusFromDetail"
        >
          {{ refreshingId === selectedRefund.id ? '查询中...' : '查询状态' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '@/services/apiClient'
import type { RefundListItem, RefundDetail, RefundStatus } from '@/types'
import { RefundStatusText, RefundStatusType } from '@/types'

// 退款列表数据
const refunds = ref<RefundListItem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 筛选器
const filterStatus = ref<string | undefined>(undefined)
const filterOutTradeNo = ref<string | undefined>(undefined)
const filterOutRefundNo = ref<string | undefined>(undefined)

// 创建退款表单
const showCreateDialog = ref(false)
const creating = ref(false)
const createForm = ref({
  payment_order_id: '',
  refund_amount: 0,
  refund_reason: ''
})
const refundAmountYuan = computed({
  get: () => createForm.value.refund_amount / 100,
  set: (val: number) => {
    createForm.value.refund_amount = Math.round(val * 100)
  }
})

// 详情对话框
const detailDialogVisible = ref(false)
const selectedRefund = ref<RefundDetail | null>(null)
const refreshingId = ref<string | null>(null)

/**
 * 获取状态标签类型
 */
function getStatusType(status: RefundStatus): string {
  return RefundStatusType[status] || 'info'
}

/**
 * 获取状态文本
 */
function getStatusText(status: RefundStatus): string {
  return RefundStatusText[status] || status
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString: string | undefined): string {
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
 * 加载退款列表
 */
async function loadRefunds() {
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
    if (filterOutRefundNo.value) {
      params.out_refund_no = filterOutRefundNo.value
    }

    const response = await apiClient.get('/admin/payment/refunds', { params })
    refunds.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载退款列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 筛选变化
 */
function handleFilterChange() {
  currentPage.value = 1
  loadRefunds()
}

/**
 * 重置筛选
 */
function handleResetFilter() {
  filterStatus.value = undefined
  filterOutTradeNo.value = undefined
  filterOutRefundNo.value = undefined
  currentPage.value = 1
  loadRefunds()
}

/**
 * 页码变化
 */
function handlePageChange() {
  loadRefunds()
}

/**
 * 每页数量变化
 */
function handleSizeChange() {
  currentPage.value = 1
  loadRefunds()
}

/**
 * 查看详情
 */
async function handleViewDetail(row: RefundListItem) {
  try {
    const response = await apiClient.get(`/admin/payment/refunds/${row.id}`)
    selectedRefund.value = response.data
    detailDialogVisible.value = true
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取退款详情失败')
  }
}

/**
 * 发起退款
 */
async function handleCreateRefund() {
  if (!createForm.value.payment_order_id) {
    ElMessage.warning('请输入支付订单ID')
    return
  }
  if (createForm.value.refund_amount <= 0) {
    ElMessage.warning('请输入退款金额')
    return
  }

  creating.value = true
  try {
    await apiClient.post('/admin/payment/refunds/create', {
      payment_order_id: createForm.value.payment_order_id,
      refund_amount: createForm.value.refund_amount,
      refund_reason: createForm.value.refund_reason
    })
    ElMessage.success('退款发起成功')
    showCreateDialog.value = false
    createForm.value = {
      payment_order_id: '',
      refund_amount: 0,
      refund_reason: ''
    }
    loadRefunds()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '发起退款失败')
  } finally {
    creating.value = false
  }
}

/**
 * 查询退款状态
 */
async function handleQueryStatus(row: RefundListItem) {
  refreshingId.value = row.id
  try {
    await apiClient.post(`/admin/payment/refunds/${row.id}/query`)
    ElMessage.success('状态已更新')
    loadRefunds()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '查询失败')
  } finally {
    refreshingId.value = null
  }
}

/**
 * 从详情对话框查询状态
 */
async function handleQueryStatusFromDetail() {
  if (!selectedRefund.value) return
  try {
    await apiClient.post(`/admin/payment/refunds/${selectedRefund.value.id}/query`)
    ElMessage.success('状态查询成功')
    // 刷新详情
    await handleViewDetail(selectedRefund.value as any)
    loadRefunds()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '查询退款状态失败')
  }
}

onMounted(() => {
  loadRefunds()
})
</script>

<style scoped>
.refund-management-page {
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

.refund-detail {
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

.text-success {
  color: #67c23a;
  font-size: 12px;
}

.text-failed {
  color: #f56c6c;
  font-size: 12px;
}
</style>
