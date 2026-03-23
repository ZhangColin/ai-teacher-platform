<template>
  <div class="enterprise-consumptions">
    <el-card class="header-card">
      <h2>消费记录</h2>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">今日消耗</div>
            <div class="stat-value today">{{ stats.today_consumed || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">本月消耗</div>
            <div class="stat-value month">{{ stats.month_consumed || 0 }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-label">总消耗</div>
            <div class="stat-value total">{{ stats.total_consumed || 0 }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="用户">
          <el-select v-model="filterForm.user_id" placeholder="全部用户" clearable filterable>
            <el-option
              v-for="user in userList"
              :key="user.user_id"
              :label="user.nickname || user.username"
              :value="user.user_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型">
          <el-select v-model="filterForm.model_name" placeholder="全部模型" clearable>
            <el-option
              v-for="model in modelList"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="handleDateChange"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadConsumptions">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
          <el-button type="success" @click="exportData">导出</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 消费记录表格 -->
    <el-card class="table-card">
      <el-table :data="consumptions" v-loading="loading" stripe>
        <el-table-column prop="created_at" label="时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="用户" width="120">
          <template #default="{ row }">
            {{ row.username || row.nickname || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="消耗积分" width="100">
          <template #default="{ row }">
            <span class="points-deducted">-{{ row.points }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="model_provider" label="供应商" width="120" />
        <el-table-column prop="model_name" label="模型" width="150" />
        <el-table-column prop="prompt_tokens" label="Prompt" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.prompt_tokens) }}
          </template>
        </el-table-column>
        <el-table-column prop="completion_tokens" label="Completion" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.completion_tokens) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_tokens" label="总计" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.total_tokens) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadConsumptions"
          @size-change="loadConsumptions"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '@/services/apiClient'

// 数据
const consumptions = ref<any[]>([])
const userList = ref<any[]>([])
const modelList = ref<string[]>([])
const stats = ref({
  today_consumed: 0,
  month_consumed: 0,
  total_consumed: 0
})
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dateRange = ref<[string, string] | null>(null)

// 筛选表单
const filterForm = reactive({
  user_id: '',
  model_name: '',
  start_date: '',
  end_date: ''
})

// 加载消费记录
const loadConsumptions = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterForm.user_id) params.user_id = filterForm.user_id
    if (filterForm.model_name) params.model_name = filterForm.model_name
    if (filterForm.start_date) params.start_date = filterForm.start_date
    if (filterForm.end_date) params.end_date = filterForm.end_date

    const response = await apiClient.get('/enterprise/consumptions', { params })
    consumptions.value = response.data.items
    total.value = response.data.total

    // 更新统计
    if (response.data.stats) {
      stats.value = response.data.stats
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载消费记录失败')
  } finally {
    loading.value = false
  }
}

// 加载用户列表（用于筛选）
const loadUserList = async () => {
  try {
    const response = await apiClient.get('/enterprise/users', {
      params: { page: 1, page_size: 1000 }
    })
    userList.value = response.data.items
  } catch (error) {
    console.error('加载用户列表失败:', error)
  }
}

// 加载模型列表（用于筛选）
const loadModelList = async () => {
  try {
    const response = await apiClient.get('/enterprise/consumptions/models')
    modelList.value = response.data.models || []
  } catch (error) {
    console.error('加载模型列表失败:', error)
  }
}

// 日期范围变化
const handleDateChange = (dates: [string, string] | null) => {
  if (dates && dates.length === 2) {
    filterForm.start_date = dates[0]
    filterForm.end_date = dates[1]
  } else {
    filterForm.start_date = ''
    filterForm.end_date = ''
  }
}

// 重置筛选
const resetFilter = () => {
  filterForm.user_id = ''
  filterForm.model_name = ''
  filterForm.start_date = ''
  filterForm.end_date = ''
  dateRange.value = null
  currentPage.value = 1
  loadConsumptions()
}

// 导出数据
const exportData = async () => {
  try {
    const params: any = {}
    if (filterForm.user_id) params.user_id = filterForm.user_id
    if (filterForm.model_name) params.model_name = filterForm.model_name
    if (filterForm.start_date) params.start_date = filterForm.start_date
    if (filterForm.end_date) params.end_date = filterForm.end_date

    const response = await apiClient.get('/enterprise/consumptions/export', {
      params,
      responseType: 'blob'
    })

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `消费记录_${new Date().toLocaleDateString()}.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '导出失败')
  }
}

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

// 格式化数字
const formatNumber = (num: number) => {
  if (!num) return '0'
  return num.toLocaleString()
}

onMounted(() => {
  loadConsumptions()
  loadUserList()
  loadModelList()
})
</script>

<style scoped>
.enterprise-consumptions {
  padding: 20px;
}

.header-card h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 10px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
}

.stat-value.today {
  color: #409eff;
}

.stat-value.month {
  color: #67c23a;
}

.stat-value.total {
  color: #e6a23c;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.points-deducted {
  color: #f56c6c;
  font-weight: 600;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
