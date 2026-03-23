<template>
  <div class="enterprise-users">
    <el-card class="header-card">
      <div class="header-content">
        <h2>用户管理</h2>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建用户
        </el-button>
      </div>
    </el-card>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm">
        <el-form-item label="用户名">
          <el-input v-model="searchForm.username" placeholder="请输入用户名" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="全部" clearable>
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-select v-model="searchForm.sort_by" placeholder="默认排序">
            <el-option label="创建时间" value="created_at" />
            <el-option label="消耗积分" value="total_consumed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadUsers">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="table-card">
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="nickname" label="昵称" width="120" />
        <el-table-column prop="email" label="邮箱" width="200" show-overflow-tooltip />
        <el-table-column label="总消耗" width="100">
          <template #default="{ row }">
            <span class="points-consumed">{{ row.total_consumed || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              link
              @click="handleToggleStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="primary" link @click="handleResetPassword(row)">
              重置密码
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
          @current-change="loadUsers"
          @size-change="loadUsers"
        />
      </div>
    </el-card>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingUser ? '编辑用户' : '创建用户'"
      width="500px"
      @close="resetForm"
    >
      <el-form :model="userForm" :rules="userRules" ref="userFormRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="userForm.username"
            placeholder="请输入用户名"
            :disabled="!!editingUser"
          />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="userForm.nickname" placeholder="请输入昵称" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!editingUser">
          <el-input
            v-model="userForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="userForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        <el-form-item label="设为管理员" prop="is_enterprise_admin">
          <el-switch v-model="userForm.is_enterprise_admin" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ editingUser ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import apiClient from '@/services/apiClient'

// 数据
const users = ref<any[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 搜索表单
const searchForm = reactive({
  username: '',
  is_active: undefined as boolean | undefined,
  sort_by: 'created_at'
})

// 创建/编辑用户
const showCreateDialog = ref(false)
const submitting = ref(false)
const editingUser = ref<any | null>(null)
const userFormRef = ref<FormInstance>()
const userForm = reactive({
  username: '',
  nickname: '',
  email: '',
  password: '',
  is_active: true,
  is_enterprise_admin: false
})
const userRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' }
  ],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6个字符', trigger: 'blur' }
  ]
}

// 加载用户列表
const loadUsers = async () => {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (searchForm.username) params.username = searchForm.username
    if (searchForm.is_active !== undefined) params.is_active = searchForm.is_active
    if (searchForm.sort_by) {
      params.sort_by = searchForm.sort_by
      params.sort_order = 'desc'
    }

    const response = await apiClient.get('/enterprise/users', { params })
    users.value = response.data.users || []
    total.value = response.data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 重置搜索
const resetSearch = () => {
  searchForm.username = ''
  searchForm.is_active = undefined
  searchForm.sort_by = 'created_at'
  currentPage.value = 1
  loadUsers()
}

// 编辑用户
const handleEdit = (user: any) => {
  editingUser.value = user
  userForm.username = user.username
  userForm.nickname = user.nickname
  userForm.email = user.email
  userForm.is_active = user.is_active
  userForm.is_enterprise_admin = user.is_enterprise_admin || false
  showCreateDialog.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!userFormRef.value) return
  await userFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (editingUser.value) {
          // 更新用户
          await apiClient.patch(`/enterprise/users/${editingUser.value.user_id}`, {
            nickname: userForm.nickname,
            email: userForm.email,
            is_active: userForm.is_active,
            is_enterprise_admin: userForm.is_enterprise_admin
          })
          ElMessage.success('用户更新成功')
        } else {
          // 创建用户
          await apiClient.post('/enterprise/users', {
            username: userForm.username,
            nickname: userForm.nickname,
            email: userForm.email,
            password: userForm.password,
            is_active: userForm.is_active,
            is_enterprise_admin: userForm.is_enterprise_admin
          })
          ElMessage.success('用户创建成功')
        }
        showCreateDialog.value = false
        resetForm()
        loadUsers()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 重置表单
const resetForm = () => {
  editingUser.value = null
  userForm.username = ''
  userForm.nickname = ''
  userForm.email = ''
  userForm.password = ''
  userForm.is_active = true
  userForm.is_enterprise_admin = false
  userFormRef.value?.clearValidate()
}

// 切换状态
const handleToggleStatus = async (user: any) => {
  const action = user.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户"${user.nickname || user.username}"吗？`, '确认', {
      type: 'warning'
    })
    await apiClient.patch(`/enterprise/users/${user.user_id}`, {
      is_active: !user.is_active
    })
    ElMessage.success(`${action}成功`)
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || `${action}失败`)
    }
  }
}

// 重置密码
const handleResetPassword = async (user: any) => {
  try {
    const result = await ElMessageBox.prompt('请输入新密码', `重置 ${user.nickname || user.username} 的密码`, {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /^.{6,}$/,
      inputErrorMessage: '密码长度至少6个字符'
    })
    const value = (result as any).value
    await apiClient.post(`/enterprise/users/${user.user_id}/reset-password`, {
      new_password: value
    })
    ElMessage.success('密码重置成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '重置密码失败')
    }
  }
}

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.enterprise-users {
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

.search-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.points-consumed {
  color: #f56c6c;
  font-weight: 600;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
