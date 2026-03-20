<template>
  <div class="admin-toolsets-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>工具集管理</h3>
          <el-button type="primary" @click="handleCreate">创建工具集</el-button>
        </div>
      </template>

      <!-- 工具集列表表格 -->
      <el-table :data="toolsets" v-loading="loading" style="width: 100%">
        <el-table-column prop="order" label="排序" width="80" />
        <el-table-column label="图标" width="80">
          <template #default="{ row }">
            <HeroIcon v-if="row.icon" :icon-name="row.icon" class="w-6 h-6" />
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="toolset_id" label="工具集ID" width="200" />
        <el-table-column prop="name" label="工具集名称" width="200" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" @click="handleMoveUp(row)" :disabled="row.order === 0">
              上移
            </el-button>
            <el-button size="small" @click="handleMoveDown(row)">下移</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑工具集对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑工具集' : '创建工具集'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="工具集ID" prop="toolset_id">
          <el-input
            v-model="form.toolset_id"
            placeholder="请输入工具集唯一标识符（如：ai_tools）"
            :disabled="isEditing"
          />
          <div class="text-xs text-gray-500 mt-1">创建后不可修改</div>
        </el-form-item>
        <el-form-item label="工具集名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入工具集名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入工具集描述"
          />
        </el-form-item>
        <el-form-item label="图标">
          <IconSelector v-model="form.icon" />
        </el-form-item>
        <el-form-item label="排序" prop="order">
          <el-input-number v-model="form.order" :min="0" :max="999" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ApiService } from '../../services/apiClient'
import type {
  AdminToolsetListItem,
  CreateToolsetRequest,
  UpdateToolsetRequest,
} from '../../types'
import IconSelector from '../../components/admin/IconSelector.vue'
import HeroIcon from '../../components/HeroIcon.vue'

// 工具集列表
const toolsets = ref<AdminToolsetListItem[]>([])
const loading = ref(false)

// 对话框
const dialogVisible = ref(false)
const isEditing = ref(false)
const formRef = ref<FormInstance>()
const submitting = ref(false)

// 表单数据
const form = reactive<CreateToolsetRequest & { id?: string }>({
  toolset_id: '',
  name: '',
  description: '',
  icon: '',
  order: 0,
})

// 表单验证规则
const rules: FormRules = {
  toolset_id: [
    { required: true, message: '请输入工具集ID', trigger: 'blur' },
    {
      pattern: /^[a-z0-9_]+$/,
      message: '工具集ID只能包含小写字母、数字和下划线',
      trigger: 'blur',
    },
  ],
  name: [
    { required: true, message: '请输入工具集名称', trigger: 'blur' },
    { min: 1, max: 50, message: '工具集名称长度为1-50个字符', trigger: 'blur' },
  ],
}

/**
 * 加载工具集列表
 */
async function loadToolsets() {
  loading.value = true
  try {
    const response = await ApiService.getAdminToolsets()
    toolsets.value = response.toolsets
  } catch (error: any) {
    ElMessage.error(error.message || '加载工具集列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 创建工具集
 */
function handleCreate() {
  isEditing.value = false
  Object.assign(form, {
    toolset_id: '',
    name: '',
    description: '',
    icon: '',
    order: toolsets.value.length,
  })
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

/**
 * 编辑工具集
 */
function handleEdit(toolset: AdminToolsetListItem) {
  isEditing.value = true
  Object.assign(form, {
    id: toolset.id,
    toolset_id: toolset.toolset_id,
    name: toolset.name,
    description: toolset.description || '',
    icon: toolset.icon || '',
    order: toolset.order,
  })
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

/**
 * 提交表单
 */
async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEditing.value && form.id) {
        // 更新
        const { id, toolset_id, ...requestData } = form
        await ApiService.updateToolset(form.toolset_id, {
          ...requestData,
          toolset_id: form.toolset_id,
        } as UpdateToolsetRequest)
        ElMessage.success('更新工具集成功')
      } else {
        // 创建
        await ApiService.createToolset(form as CreateToolsetRequest)
        ElMessage.success('创建工具集成功')
      }
      dialogVisible.value = false
      loadToolsets()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

/**
 * 上移工具集
 */
async function handleMoveUp(toolset: AdminToolsetListItem) {
  try {
    await ApiService.moveToolsetUp(toolset.toolset_id)
    ElMessage.success('上移成功')
    loadToolsets()
  } catch (error: any) {
    ElMessage.error(error.message || '上移失败')
  }
}

/**
 * 下移工具集
 */
async function handleMoveDown(toolset: AdminToolsetListItem) {
  try {
    await ApiService.moveToolsetDown(toolset.toolset_id)
    ElMessage.success('下移成功')
    loadToolsets()
  } catch (error: any) {
    ElMessage.error(error.message || '下移失败')
  }
}

/**
 * 删除工具集
 */
async function handleDelete(toolset: AdminToolsetListItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除工具集 "${toolset.name}" 吗？删除后无法恢复。`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    loading.value = true
    try {
      await ApiService.deleteToolset(toolset.toolset_id)
      ElMessage.success('删除工具集成功')
      loadToolsets()
    } catch (error: any) {
      ElMessage.error(error.message || '删除工具集失败')
    } finally {
      loading.value = false
    }
  } catch {
    // 用户取消
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadToolsets()
})
</script>

<style scoped>
.admin-toolsets-page {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}
</style>
