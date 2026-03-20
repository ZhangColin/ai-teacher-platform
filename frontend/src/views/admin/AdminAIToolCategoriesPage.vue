<template>
  <div class="admin-ai-tool-categories-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>AI工具分类管理</h3>
          <el-button type="primary" @click="handleCreate">创建分类</el-button>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filter-bar">
        <el-select
          v-model="filterToolsetId"
          placeholder="筛选工具集"
          clearable
          @change="handleFilterChange"
          style="width: 200px"
        >
          <el-option
            v-for="toolset in toolsets"
            :key="toolset.id"
            :label="toolset.name"
            :value="toolset.id"
          />
        </el-select>
      </div>

      <!-- 分类列表表格 -->
      <el-table :data="categories" v-loading="loading" style="width: 100%; margin-top: 16px">
        <el-table-column prop="order" label="排序" width="80" />
        <el-table-column label="图标" width="80">
          <template #default="{ row }">
            <HeroIcon v-if="row.icon" :icon-name="row.icon" class="w-6 h-6" />
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="toolset_name" label="所属工具集" width="200" />
        <el-table-column prop="name" label="分类名称" width="200" />
        <el-table-column prop="tool_count" label="工具数量" width="100" />
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

    <!-- 创建/编辑分类对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑分类' : '创建分类'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="所属工具集" prop="toolset_id">
          <el-select
            v-model="form.toolset_id"
            placeholder="请选择工具集"
            style="width: 100%"
          >
            <el-option
              v-for="toolset in toolsets"
              :key="toolset.id"
              :label="toolset.name"
              :value="toolset.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入分类名称" />
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
  AdminAIToolCategoryListItem,
  AdminToolsetListItem,
  CreateAIToolCategoryRequest,
  UpdateAIToolCategoryRequest,
} from '../../types'
import IconSelector from '../../components/admin/IconSelector.vue'
import HeroIcon from '../../components/HeroIcon.vue'

// 分类列表
const categories = ref<AdminAIToolCategoryListItem[]>([])
const toolsets = ref<AdminToolsetListItem[]>([])
const loading = ref(false)

// 筛选器
const filterToolsetId = ref<string>()

// 对话框
const dialogVisible = ref(false)
const isEditing = ref(false)
const formRef = ref<FormInstance>()
const submitting = ref(false)

// 表单数据
const form = reactive<CreateAIToolCategoryRequest & { id?: string }>({
  toolset_id: '',
  name: '',
  icon: '',
  order: 0,
})

// 表单验证规则
const rules: FormRules = {
  toolset_id: [{ required: true, message: '请选择所属工具集', trigger: 'change' }],
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { min: 1, max: 50, message: '分类名称长度为1-50个字符', trigger: 'blur' },
  ],
}

/**
 * 加载工具集列表
 */
async function loadToolsets() {
  try {
    const response = await ApiService.getAdminToolsets()
    toolsets.value = response.toolsets
  } catch (error: any) {
    ElMessage.error(error.message || '加载工具集列表失败')
  }
}

/**
 * 加载分类列表
 */
async function loadCategories() {
  loading.value = true
  try {
    const response = await ApiService.getAdminAIToolCategories()
    let filteredCategories = response.categories

    if (filterToolsetId.value) {
      filteredCategories = filteredCategories.filter(
        (c) => c.toolset_id === filterToolsetId.value
      )
    }

    categories.value = filteredCategories
  } catch (error: any) {
    ElMessage.error(error.message || '加载分类列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 筛选变化
 */
function handleFilterChange() {
  loadCategories()
}

/**
 * 创建分类
 */
function handleCreate() {
  isEditing.value = false
  Object.assign(form, {
    toolset_id: filterToolsetId.value || '',
    name: '',
    icon: '',
    order: categories.value.length,
  })
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

/**
 * 编辑分类
 */
function handleEdit(category: AdminAIToolCategoryListItem) {
  isEditing.value = true
  Object.assign(form, {
    id: category.id,
    toolset_id: category.toolset_id,
    name: category.name,
    icon: category.icon || '',
    order: category.order,
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
        const { id, ...requestData } = form
        await ApiService.updateAIToolCategory(form.id, requestData as UpdateAIToolCategoryRequest)
        ElMessage.success('更新分类成功')
      } else {
        // 创建
        await ApiService.createAIToolCategory(form as CreateAIToolCategoryRequest)
        ElMessage.success('创建分类成功')
      }
      dialogVisible.value = false
      loadCategories()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

/**
 * 上移分类
 */
async function handleMoveUp(category: AdminAIToolCategoryListItem) {
  try {
    await ApiService.moveAIToolCategoryUp(category.id)
    ElMessage.success('上移成功')
    loadCategories()
  } catch (error: any) {
    ElMessage.error(error.message || '上移失败')
  }
}

/**
 * 下移分类
 */
async function handleMoveDown(category: AdminAIToolCategoryListItem) {
  try {
    await ApiService.moveAIToolCategoryDown(category.id)
    ElMessage.success('下移成功')
    loadCategories()
  } catch (error: any) {
    ElMessage.error(error.message || '下移失败')
  }
}

/**
 * 删除分类
 */
async function handleDelete(category: AdminAIToolCategoryListItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除分类 "${category.name}" 吗？删除后无法恢复。`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    loading.value = true
    try {
      await ApiService.deleteAIToolCategory(category.id)
      ElMessage.success('删除分类成功')
      loadCategories()
    } catch (error: any) {
      ElMessage.error(error.message || '删除分类失败')
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
  loadCategories()
})
</script>

<style scoped>
.admin-ai-tool-categories-page {
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

.filter-bar {
  display: flex;
  gap: 12px;
}
</style>
