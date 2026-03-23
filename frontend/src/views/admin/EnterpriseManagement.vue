<template>
  <div class="enterprise-management">
    <el-card class="header-card">
      <div class="header-content">
        <h2>企业管理</h2>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建企业
        </el-button>
      </div>
    </el-card>

    <!-- 企业列表 -->
    <el-card class="table-card">
      <el-table :data="enterprises" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="200" />
        <el-table-column prop="name" label="企业名称" width="200" />
        <el-table-column prop="code" label="企业代码" width="150" />
        <el-table-column label="总积分" width="120">
          <template #default="{ row }">
            <span class="total-points">{{ row.total_points }}</span>
          </template>
        </el-table-column>
        <el-table-column label="赠送积分" width="120">
          <template #default="{ row }">
            <span class="gratis-points">{{ row.balance_gratis }}</span>
          </template>
        </el-table-column>
        <el-table-column label="充值积分" width="120">
          <template #default="{ row }">
            <span class="paid-points">{{ row.balance_paid }}</span>
          </template>
        </el-table-column>
        <el-table-column label="负债积分" width="120">
          <template #default="{ row }">
            <span class="debt-points">{{ row.debt_points }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="user_count" label="用户数" width="100" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleAddPoints(row)">
              充值
            </el-button>
            <el-button size="small" type="primary" link @click="handleViewConsumption(row)">
              消费
            </el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              link
              @click="handleToggleStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              link
              @click="handleDelete(row)"
              :disabled="row.user_count > 0"
            >
              删除
            </el-button>
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
          @current-change="loadEnterprises"
          @size-change="loadEnterprises"
        />
      </div>
    </el-card>

    <!-- 创建企业对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建企业"
      width="500px"
      @close="resetCreateForm"
    >
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="企业名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入企业名称" />
        </el-form-item>
        <el-form-item label="企业代码" prop="code">
          <el-input v-model="createForm.code" placeholder="请输入企业代码（英文）" />
        </el-form-item>
        <el-form-item label="初始赠送积分" prop="initial_gratis">
          <el-input-number
            v-model="createForm.initial_gratis"
            :min="0"
            :max="1000000"
            :step="100"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- 充值对话框 -->
    <el-dialog
      v-model="showAddPointsDialog"
      title="企业充值"
      width="500px"
      @close="resetAddPointsForm"
    >
      <div class="enterprise-info">
        <p><strong>企业：</strong>{{ currentEnterprise?.name }}</p>
        <p><strong>当前积分：</strong>{{ currentEnterprise?.total_points }}</p>
      </div>
      <el-form :model="addPointsForm" :rules="addPointsRules" ref="addPointsFormRef" label-width="100px">
        <el-form-item label="充值类型" prop="source_type">
          <el-radio-group v-model="addPointsForm.source_type">
            <el-radio label="admin_recharge">管理员充值</el-radio>
            <el-radio label="recharge">用户充值</el-radio>
            <el-radio label="event_bonus">活动赠送</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="充值数量" prop="amount">
          <el-input-number
            v-model="addPointsForm.amount"
            :min="1"
            :max="10000000"
            :step="100"
          />
        </el-form-item>
        <el-form-item label="备注" prop="note">
          <el-input
            v-model="addPointsForm.note"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddPointsDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddPointsSubmit" :loading="addingPoints">
          确认充值
        </el-button>
      </template>
    </el-dialog>

    <!-- 消费记录对话框 -->
    <el-dialog
      v-model="showConsumptionDialog"
      title="消费记录"
      width="900px"
    >
      <div class="enterprise-info">
        <p><strong>企业：</strong>{{ currentEnterprise?.name }}</p>
      </div>
      <el-table :data="consumptions" v-loading="loadingConsumptions" stripe max-height="400">
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="points" label="消耗积分" width="100">
          <template #default="{ row }">
            <span class="points-deducted">-{{ row.points }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="model_provider" label="模型供应商" width="120" />
        <el-table-column prop="model_name" label="模型名称" width="150" />
        <el-table-column prop="prompt_tokens" label="Prompt Tokens" width="120" />
        <el-table-column prop="completion_tokens" label="Completion Tokens" width="140" />
        <el-table-column prop="user_id" label="用户ID" width="200" />
      </el-table>
      <div class="pagination">
        <el-pagination
          v-model:current-page="consumptionPage"
          v-model:page-size="consumptionPageSize"
          :total="consumptionTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="loadConsumptions"
          @size-change="loadConsumptions"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import apiClient from '@/services/apiClient'
import type { EnterpriseInfo } from '@/types'

// 数据
const enterprises = ref<EnterpriseInfo[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 创建企业
const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  name: '',
  code: '',
  initial_gratis: 0
})
const createRules: FormRules = {
  name: [{ required: true, message: '请输入企业名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入企业代码', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '企业代码只能包含字母、数字、下划线和连字符', trigger: 'blur' }
  ]
}

// 充值
const showAddPointsDialog = ref(false)
const addingPoints = ref(false)
const addPointsFormRef = ref<FormInstance>()
const currentEnterprise = ref<EnterpriseInfo | null>(null)
const addPointsForm = reactive({
  amount: 1000,
  source_type: 'admin_recharge',
  note: ''
})
const addPointsRules: FormRules = {
  amount: [{ required: true, message: '请输入充值数量', trigger: 'blur' }],
  source_type: [{ required: true, message: '请选择充值类型', trigger: 'change' }]
}

// 消费记录
const showConsumptionDialog = ref(false)
const consumptions = ref<any[]>([])
const loadingConsumptions = ref(false)
const consumptionPage = ref(1)
const consumptionPageSize = ref(20)
const consumptionTotal = ref(0)

// 加载企业列表
const loadEnterprises = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/admin/enterprises', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    enterprises.value = response.data.items
    total.value = response.data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载企业列表失败')
  } finally {
    loading.value = false
  }
}

// 创建企业
const handleCreate = async () => {
  if (!createFormRef.value) return
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      creating.value = true
      try {
        await apiClient.post('/admin/enterprises', {
          name: createForm.name,
          code: createForm.code,
          initial_gratis: createForm.initial_gratis
        })
        ElMessage.success('企业创建成功')
        showCreateDialog.value = false
        resetCreateForm()
        loadEnterprises()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '创建企业失败')
      } finally {
        creating.value = false
      }
    }
  })
}

// 重置创建表单
const resetCreateForm = () => {
  createForm.name = ''
  createForm.code = ''
  createForm.initial_gratis = 0
  createFormRef.value?.clearValidate()
}

// 充值
const handleAddPoints = (enterprise: EnterpriseInfo) => {
  currentEnterprise.value = enterprise
  addPointsForm.amount = 1000
  addPointsForm.source_type = 'admin_recharge'
  addPointsForm.note = ''
  showAddPointsDialog.value = true
}

// 提交充值
const handleAddPointsSubmit = async () => {
  if (!addPointsFormRef.value || !currentEnterprise.value) return
  await addPointsFormRef.value.validate(async (valid) => {
    if (valid) {
      addingPoints.value = true
      try {
        await apiClient.post(`/admin/enterprises/${currentEnterprise.value.id}/add-points`, {
          amount: addPointsForm.amount,
          source_type: addPointsForm.source_type,
          note: addPointsForm.note
        })
        ElMessage.success('充值成功')
        showAddPointsDialog.value = false
        loadEnterprises()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '充值失败')
      } finally {
        addingPoints.value = false
      }
    }
  })
}

// 重置充值表单
const resetAddPointsForm = () => {
  addPointsForm.amount = 1000
  addPointsForm.source_type = 'admin_recharge'
  addPointsForm.note = ''
  addPointsFormRef.value?.clearValidate()
}

// 查看消费记录
const handleViewConsumption = async (enterprise: EnterpriseInfo) => {
  currentEnterprise.value = enterprise
  consumptionPage.value = 1
  showConsumptionDialog.value = true
  loadConsumptions()
}

// 加载消费记录
const loadConsumptions = async () => {
  if (!currentEnterprise.value) return
  loadingConsumptions.value = true
  try {
    const response = await apiClient.get(`/admin/enterprises/${currentEnterprise.value.id}/consumptions`, {
      params: {
        page: consumptionPage.value,
        page_size: consumptionPageSize.value
      }
    })
    consumptions.value = response.data.items
    consumptionTotal.value = response.data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载消费记录失败')
  } finally {
    loadingConsumptions.value = false
  }
}

// 切换状态
const handleToggleStatus = async (enterprise: EnterpriseInfo) => {
  const action = enterprise.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}企业"${enterprise.name}"吗？`, '确认', {
      type: 'warning'
    })
    await apiClient.patch(`/admin/enterprises/${enterprise.id}`, {
      is_active: !enterprise.is_active
    })
    ElMessage.success(`${action}成功`)
    loadEnterprises()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || `${action}失败`)
    }
  }
}

// 删除企业
const handleDelete = async (enterprise: EnterpriseInfo) => {
  if (enterprise.user_count > 0) {
    ElMessage.warning('该企业还有用户，无法删除')
    return
  }
  try {
    await ElMessageBox.confirm(`确定要删除企业"${enterprise.name}"吗？此操作不可恢复！`, '确认删除', {
      type: 'warning'
    })
    await apiClient.delete(`/admin/enterprises/${enterprise.id}`)
    ElMessage.success('删除成功')
    loadEnterprises()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

onMounted(() => {
  loadEnterprises()
})
</script>

<style scoped>
.enterprise-management {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.table-card {
  margin-bottom: 20px;
}

.total-points {
  font-weight: 600;
  color: #409eff;
}

.gratis-points {
  color: #67c23a;
}

.paid-points {
  color: #e6a23c;
}

.debt-points {
  color: #f56c6c;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.enterprise-info {
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 20px;
}

.enterprise-info p {
  margin: 5px 0;
  font-size: 14px;
}

.points-deducted {
  color: #f56c6c;
  font-weight: 600;
}
</style>
