<template>
  <div class="recharge-management-page">
    <el-card>
      <template #header>
        <h3>充值管理</h3>
      </template>

      <!-- 筛选器 -->
      <div class="filter-bar">
        <el-select
          v-model="filterEnterpriseId"
          placeholder="筛选企业"
          clearable
          @change="handleFilterChange"
          style="width: 200px"
        >
          <el-option
            v-for="enterprise in enterprises"
            :key="enterprise.id"
            :label="enterprise.name"
            :value="enterprise.id"
          />
        </el-select>
      </div>

      <!-- 充值记录表格 -->
      <el-table
        :data="records"
        v-loading="loading"
        style="width: 100%; margin-top: 16px"
      >
        <el-table-column prop="enterprise_name" label="企业名称" width="180" />
        <el-table-column prop="amount" label="充值数量" width="110">
          <template #default="{ row }">
            <span :class="{ 'text-green': row.amount > 0 }">+{{ row.amount }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="source_type" label="类型" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.source_type === 'offline_payment'" type="primary">线下支付</el-tag>
            <el-tag v-else-if="row.source_type === 'online_payment'" type="success">线上支付</el-tag>
            <el-tag v-else-if="row.source_type === 'admin_gift'" type="success">赠送</el-tag>
            <el-tag v-else-if="row.source_type === 'admin_adjust'" type="warning">管理员调整</el-tag>
            <el-tag v-else type="info">{{ row.source_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="120">
          <template #default="{ row }">
            {{ row.operator_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="180">
          <template #default="{ row }">
            {{ row.remark || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '@/services/apiClient'

// 充值记录数据
const records = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 企业列表
const enterprises = ref<{ id: string; name: string }[]>([])

// 筛选器
const filterEnterpriseId = ref<string | undefined>(undefined)

/**
 * 加载企业列表
 */
async function loadEnterprises() {
  try {
    const response = await apiClient.get('/admin/enterprises', {
      params: { page: 1, page_size: 100 }
    })
    enterprises.value = response.data.enterprises.map((e: any) => ({
      id: e.id,
      name: e.name
    }))
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载企业列表失败')
  }
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString: string): string {
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
 * 加载充值记录
 */
async function loadRecords() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterEnterpriseId.value) {
      params.enterprise_id = filterEnterpriseId.value
    }

    const response = await apiClient.get('/admin/enterprises/point-transactions', { params })
    records.value = response.data.items.map((item: any) => ({
      ...item,
      enterprise_name: item.enterprise_name || '-'
    }))
    total.value = response.data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载充值记录失败')
  } finally {
    loading.value = false
  }
}

/**
 * 筛选变化
 */
function handleFilterChange() {
  currentPage.value = 1
  loadRecords()
}

/**
 * 页码变化
 */
function handlePageChange() {
  loadRecords()
}

/**
 * 每页数量变化
 */
function handleSizeChange() {
  currentPage.value = 1
  loadRecords()
}

// 组件挂载时加载数据
onMounted(() => {
  loadEnterprises()
  loadRecords()
})
</script>

<style scoped>
.recharge-management-page {
  width: 100%;
}

.filter-bar {
  display: flex;
  gap: 12px;
}

.text-green {
  color: #67c23a;
  font-weight: 600;
}
</style>
