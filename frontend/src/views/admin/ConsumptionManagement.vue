<template>
  <div class="consumption-management-page">
    <el-card>
      <template #header>
        <h3>消费管理</h3>
      </template>

      <!-- 筛选器 -->
      <div class="filter-bar">
        <el-select
          v-model="filterEnterpriseId"
          placeholder="筛选企业"
          clearable
          @change="handleEnterpriseChange"
          style="width: 200px"
        >
          <el-option
            v-for="enterprise in enterprises"
            :key="enterprise.id"
            :label="enterprise.name"
            :value="enterprise.id"
          />
        </el-select>
        <el-select
          v-model="filterUserId"
          placeholder="筛选用户"
          clearable
          @change="handleFilterChange"
          style="width: 200px"
          :disabled="!filterEnterpriseId"
        >
          <el-option
            v-for="user in users"
            :key="user.user_id"
            :label="user.username"
            :value="user.user_id"
          />
        </el-select>
      </div>

      <!-- 消费记录表格 -->
      <el-table
        :data="records"
        v-loading="loading"
        style="width: 100%; margin-top: 16px"
      >
        <el-table-column prop="enterprise_name" label="企业名称" width="180" />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="total_points" label="消耗积分" width="100">
          <template #default="{ row }">
            <span class="text-red">-{{ row.total_points }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="model_provider" label="模型供应商" width="120">
          <template #default="{ row }">
            {{ row.model_provider || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="model_name" label="模型名称" width="150">
          <template #default="{ row }">
            {{ row.model_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="prompt_tokens" label="Prompt Tokens" width="120">
          <template #default="{ row }">
            {{ row.prompt_tokens?.toLocaleString() || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="completion_tokens" label="Completion Tokens" width="140">
          <template #default="{ row }">
            {{ row.completion_tokens?.toLocaleString() || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="消费时间" width="180">
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

// 消费记录数据
const records = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 企业列表
const enterprises = ref<{ id: string; name: string }[]>([])

// 用户列表
const users = ref<{ user_id: string; username: string }[]>([])

// 筛选器
const filterEnterpriseId = ref<string | undefined>(undefined)
const filterUserId = ref<string | undefined>(undefined)

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
 * 加载用户列表
 */
async function loadUsers() {
  if (!filterEnterpriseId.value) {
    users.value = []
    return
  }
  try {
    const response = await apiClient.get('/admin/users', {
      params: { page: 1, page_size: 1000, enterprise_id: filterEnterpriseId.value }
    })
    users.value = response.data.users.map((u: any) => ({
      user_id: u.user_id,
      username: u.username
    }))
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载用户列表失败')
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
 * 加载消费记录
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
    if (filterUserId.value) {
      params.user_id = filterUserId.value
    }

    const response = await apiClient.get('/admin/enterprises/consumptions', { params })
    records.value = response.data.items.map((item: any) => ({
      ...item,
      enterprise_name: item.enterprise_name || '-',
      username: item.username || '-'
    }))
    total.value = response.data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载消费记录失败')
  } finally {
    loading.value = false
  }
}

/**
 * 企业筛选变化
 */
function handleEnterpriseChange() {
  filterUserId.value = undefined
  users.value = []
  if (filterEnterpriseId.value) {
    loadUsers()
  }
  currentPage.value = 1
  loadRecords()
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
.consumption-management-page {
  width: 100%;
}

.filter-bar {
  display: flex;
  gap: 12px;
}

.text-red {
  color: #f56c6c;
  font-weight: 600;
}
</style>
