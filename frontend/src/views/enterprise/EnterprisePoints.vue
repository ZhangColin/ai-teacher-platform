<template>
  <div class="enterprise-points">
    <el-card class="header-card">
      <h2>积分管理</h2>
    </el-card>

    <!-- 积分概览 -->
    <el-card class="overview-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item total">
            <div class="stat-value">{{ enterpriseInfo?.total_points || 0 }}</div>
            <div class="stat-label">总积分</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item gratis">
            <div class="stat-value">{{ enterpriseInfo?.balance_gratis || 0 }}</div>
            <div class="stat-label">赠送积分</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item paid">
            <div class="stat-value">{{ enterpriseInfo?.balance_paid || 0 }}</div>
            <div class="stat-label">充值积分</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item debt">
            <div class="stat-value">{{ enterpriseInfo?.debt_points || 0 }}</div>
            <div class="stat-label">负债积分</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 积分交易记录 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>积分交易记录</span>
          <el-radio-group v-model="transactionFilter" size="small" @change="loadTransactions">
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button label="gratis">赠送</el-radio-button>
            <el-radio-button label="paid">充值</el-radio-button>
            <el-radio-button label="admin_recharge">管理员充值</el-radio-button>
            <el-radio-button label="event_bonus">活动赠送</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <el-table :data="transactions" v-loading="loading" stripe>
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeColor(row.source_type)" size="small">
              {{ getTypeLabel(row.source_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="积分变动" width="120">
          <template #default="{ row }">
            <span :class="row.amount > 0 ? 'points-add' : 'points-deduct'">
              {{ row.amount > 0 ? '+' : '' }}{{ row.amount }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="balance_after" label="交易后余额" width="120" />
        <el-table-column prop="note" label="备注" show-overflow-tooltip />
        <el-table-column prop="admin_username" label="操作人" width="120" />
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadTransactions"
          @size-change="loadTransactions"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { ElMessage } from 'element-plus'
import apiClient from '@/services/apiClient'
import type { EnterpriseInfo } from '@/types'

const authStore = useAuthStore()

const enterpriseInfo = ref<EnterpriseInfo | null>(null)
const transactions = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const transactionFilter = ref('')

// 获取企业ID
const enterpriseId = computed(() => authStore.user?.enterprise_id)

// 加载企业信息
const loadEnterpriseInfo = async () => {
  if (!enterpriseId.value) return
  try {
    const response = await apiClient.get(`/enterprise/enterprises/${enterpriseId.value}`)
    enterpriseInfo.value = response.data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载企业信息失败')
  }
}

// 加载交易记录
const loadTransactions = async () => {
  if (!enterpriseId.value) return
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (transactionFilter.value) {
      params.source_type = transactionFilter.value
    }

    const response = await apiClient.get(`/enterprise/enterprises/${enterpriseId.value}/transactions`, { params })
    transactions.value = response.data.items
    total.value = response.data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载交易记录失败')
  } finally {
    loading.value = false
  }
}

// 获取类型标签
const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    gratis: '赠送',
    paid: '充值',
    admin_recharge: '管理员充值',
    recharge: '用户充值',
    event_bonus: '活动赠送',
    register_bonus: '注册赠送'
  }
  return labels[type] || type
}

// 获取类型颜色
const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    gratis: 'success',
    paid: 'warning',
    admin_recharge: 'primary',
    recharge: 'warning',
    event_bonus: 'success',
    register_bonus: 'success'
  }
  return colors[type] || 'info'
}

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

onMounted(() => {
  loadEnterpriseInfo()
  loadTransactions()
})
</script>

<style scoped>
.enterprise-points {
  padding: 20px;
}

.header-card h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.overview-card {
  margin-bottom: 20px;
}

.stat-item {
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.stat-item.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-item.gratis {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
  color: #333;
}

.stat-item.paid {
  background: linear-gradient(135deg, #fccb90 0%, #d57eeb 100%);
  color: white;
}

.stat-item.debt {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
  color: #333;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 8px;
}

.table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.points-add {
  color: #67c23a;
  font-weight: 600;
}

.points-deduct {
  color: #f56c6c;
  font-weight: 600;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
