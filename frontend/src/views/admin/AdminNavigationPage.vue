<template>
  <div class="admin-navigation-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>导航模块管理</h3>
          <el-button type="primary" @click="handleCreate">创建导航模块</el-button>
        </div>
      </template>

      <!-- 导航模块列表表格 -->
      <el-table :data="modules" v-loading="loading" style="width: 100%">
        <el-table-column prop="order" label="排序" width="80" />
        <el-table-column label="图标" width="80">
          <template #default="{ row }">
            <HeroIcon v-if="row.icon" :icon-name="row.icon" class="w-6 h-6" />
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="模块名称" width="200" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.type === 'toolset' || row.type === 'ai_tools' ? 'primary' : 'success'">
              {{ row.type === 'toolset' || row.type === 'ai_tools' ? '工具集' : '页面' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="配置来源/页面路径" min-width="200">
          <template #default="{ row }">
            <span v-if="row.type === 'toolset' || row.type === 'ai_tools'">{{ row.config_source || '-' }}</span>
            <span v-else>{{ row.page_path || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.type === 'toolset' || row.type === 'ai_tools'"
              size="small"
              @click="handleShowCategories(row)"
            >
              分类
            </el-button>
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

    <!-- 创建/编辑导航模块对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑导航模块' : '创建导航模块'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="模块名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模块名称" />
        </el-form-item>
        <el-form-item label="模块类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio value="toolset">工具集</el-radio>
            <el-radio value="page">独立页面</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item
          label="配置来源"
          prop="config_source"
          v-if="form.type === 'toolset'"
        >
          <el-input
            v-model="form.config_source"
            placeholder="请输入配置来源（如：tools/ai_tools）"
          />
        </el-form-item>
        <el-form-item label="页面路径" prop="page_path" v-else>
          <el-input
            v-model="form.page_path"
            placeholder="请输入页面路径（如：/common-tools）"
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

    <!-- 分类管理对话框 -->
    <el-dialog
      v-model="categoriesDialogVisible"
      :title="`${currentModule?.name} - 分类管理`"
      width="800px"
    >
      <div class="categories-header">
        <el-button type="primary" size="small" @click="handleCreateCategory">添加分类</el-button>
      </div>
      <el-table :data="categories" v-loading="categoriesLoading" size="small">
        <el-table-column prop="order" label="排序" width="80" />
        <el-table-column label="图标" width="60">
          <template #default="{ row }">
            <HeroIcon v-if="row.icon" :icon-name="row.icon" class="w-5 h-5" />
          </template>
        </el-table-column>
        <el-table-column prop="name" label="分类名称" />
        <el-table-column prop="tool_count" label="工具数量" width="100" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEditCategory(row)">编辑</el-button>
            <el-button link type="primary" size="small" @click="handleMoveCategoryUp(row)" :disabled="row.order === 0">上移</el-button>
            <el-button link type="primary" size="small" @click="handleMoveCategoryDown(row)">下移</el-button>
            <el-button link type="danger" size="small" @click="handleDeleteCategory(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 创建/编辑分类对话框 -->
    <el-dialog
      v-model="categoryFormDialogVisible"
      :title="isEditingCategory ? '编辑分类' : '添加分类'"
      width="500px"
    >
      <el-form ref="categoryFormRef" :model="categoryForm" :rules="categoryRules" label-width="100px">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="categoryForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="图标">
          <IconSelector v-model="categoryForm.icon" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="categoryForm.order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="categoryFormDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitCategory" :loading="categorySubmitting">
          {{ isEditingCategory ? '保存' : '创建' }}
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
  AdminNavigationModuleListItem,
  AdminNavigationModuleCategoryListItem,
  CreateNavigationModuleRequest,
  UpdateNavigationModuleRequest,
  CreateNavigationModuleCategoryRequest,
  UpdateNavigationModuleCategoryRequest,
} from '../../types'
import IconSelector from '../../components/admin/IconSelector.vue'
import HeroIcon from '../../components/HeroIcon.vue'

// 导航模块列表
const modules = ref<AdminNavigationModuleListItem[]>([])
const loading = ref(false)

// 对话框
const dialogVisible = ref(false)
const isEditing = ref(false)
const formRef = ref<FormInstance>()
const submitting = ref(false)

// 表单数据
const form = reactive<CreateNavigationModuleRequest & { id?: string }>({
  name: '',
  type: 'toolset',
  config_source: '',
  page_path: '',
  icon: '',
  order: 0,
})

// 表单验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入模块名称', trigger: 'blur' },
    { min: 1, max: 50, message: '模块名称长度为1-50个字符', trigger: 'blur' },
  ],
  type: [{ required: true, message: '请选择模块类型', trigger: 'change' }],
  config_source: [
    {
      validator: (_rule, value, callback) => {
        if (form.type === 'toolset' && !value) {
          callback(new Error('工具集类型必须指定配置来源'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  page_path: [
    {
      validator: (_rule, value, callback) => {
        if (form.type === 'page' && !value) {
          callback(new Error('页面类型必须指定页面路径'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// ==================== 分类管理 ====================
const currentModule = ref<AdminNavigationModuleListItem | null>(null)
const categories = ref<AdminNavigationModuleCategoryListItem[]>([])
const categoriesDialogVisible = ref(false)
const categoriesLoading = ref(false)

// 分类表单
const categoryFormDialogVisible = ref(false)
const isEditingCategory = ref(false)
const categoryFormRef = ref<FormInstance>()
const categorySubmitting = ref(false)
const categoryForm = ref<CreateNavigationModuleCategoryRequest & { id?: string }>({
  name: '',
  icon: '',
  order: 0,
})

const categoryRules: FormRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { min: 1, max: 50, message: '分类名称长度为1-50个字符', trigger: 'blur' },
  ],
}

/**
 * 加载导航模块列表
 */
async function loadModules() {
  loading.value = true
  try {
    const response = await ApiService.getAdminNavigationModules()
    modules.value = response.modules
  } catch (error: any) {
    ElMessage.error(error.message || '加载导航模块列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 创建导航模块
 */
function handleCreate() {
  isEditing.value = false
  Object.assign(form, {
    name: '',
    type: 'toolset',
    config_source: '',
    page_path: '',
    icon: '',
    order: modules.value.length,
  })
  formRef.value?.clearValidate()
  dialogVisible.value = true
}

/**
 * 编辑导航模块
 */
function handleEdit(module: AdminNavigationModuleListItem) {
  isEditing.value = true
  Object.assign(form, {
    id: module.id,
    name: module.name,
    type: module.type,
    config_source: module.config_source || '',
    page_path: module.page_path || '',
    icon: module.icon || '',
    order: module.order,
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
        await ApiService.updateNavigationModule(id, requestData as UpdateNavigationModuleRequest)
        ElMessage.success('更新导航模块成功')
      } else {
        // 创建
        await ApiService.createNavigationModule(form as CreateNavigationModuleRequest)
        ElMessage.success('创建导航模块成功')
      }
      dialogVisible.value = false
      loadModules()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

/**
 * 上移导航模块
 */
async function handleMoveUp(module: AdminNavigationModuleListItem) {
  try {
    await ApiService.moveNavigationModuleUp(module.id)
    ElMessage.success('上移成功')
    loadModules()
  } catch (error: any) {
    ElMessage.error(error.message || '上移失败')
  }
}

/**
 * 下移导航模块
 */
async function handleMoveDown(module: AdminNavigationModuleListItem) {
  try {
    await ApiService.moveNavigationModuleDown(module.id)
    ElMessage.success('下移成功')
    loadModules()
  } catch (error: any) {
    ElMessage.error(error.message || '下移失败')
  }
}

/**
 * 删除导航模块
 */
async function handleDelete(module: AdminNavigationModuleListItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除导航模块 "${module.name}" 吗？删除后无法恢复。`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    loading.value = true
    try {
      await ApiService.deleteNavigationModule(module.id)
      ElMessage.success('删除导航模块成功')
      loadModules()
    } catch (error: any) {
      ElMessage.error(error.message || '删除导航模块失败')
    } finally {
      loading.value = false
    }
  } catch {
    // 用户取消
  }
}

/**
 * 显示分类管理对话框
 */
async function handleShowCategories(module: AdminNavigationModuleListItem) {
  currentModule.value = module
  categoriesDialogVisible.value = true
  await loadCategories(module.id)
}

/**
 * 加载分类列表
 */
async function loadCategories(moduleId: string) {
  categoriesLoading.value = true
  try {
    const response = await ApiService.getAdminNavigationModuleCategories(moduleId)
    categories.value = response.categories
  } catch (error: any) {
    ElMessage.error(error.message || '加载分类列表失败')
  } finally {
    categoriesLoading.value = false
  }
}

/**
 * 创建分类
 */
function handleCreateCategory() {
  if (!currentModule.value) return
  isEditingCategory.value = false
  categoryForm.value = {
    name: '',
    icon: '',
    order: categories.value.length,
  }
  categoryFormRef.value?.clearValidate()
  categoryFormDialogVisible.value = true
}

/**
 * 编辑分类
 */
function handleEditCategory(category: AdminNavigationModuleCategoryListItem) {
  if (!currentModule.value) return
  isEditingCategory.value = true
  categoryForm.value = {
    id: category.id,
    name: category.name,
    icon: category.icon || '',
    order: category.order,
  }
  categoryFormRef.value?.clearValidate()
  categoryFormDialogVisible.value = true
}

/**
 * 提交分类表单
 */
async function handleSubmitCategory() {
  if (!categoryFormRef.value || !currentModule.value) return

  await categoryFormRef.value.validate(async (valid) => {
    if (!valid) return

    categorySubmitting.value = true
    try {
      if (isEditingCategory.value && categoryForm.value.id) {
        // 更新
        const { id, ...requestData } = categoryForm.value
        await ApiService.updateNavigationModuleCategory(
          currentModule.value.id,
          id,
          requestData as UpdateNavigationModuleCategoryRequest
        )
        ElMessage.success('更新分类成功')
      } else {
        // 创建
        await ApiService.createNavigationModuleCategory(
          currentModule.value.id,
          categoryForm.value as CreateNavigationModuleCategoryRequest
        )
        ElMessage.success('创建分类成功')
      }
      categoryFormDialogVisible.value = false
      await loadCategories(currentModule.value.id)
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      categorySubmitting.value = false
    }
  })
}

/**
 * 上移分类
 */
async function handleMoveCategoryUp(category: AdminNavigationModuleCategoryListItem) {
  if (!currentModule.value) return
  try {
    await ApiService.moveNavigationModuleCategoryUp(currentModule.value.id, category.id)
    ElMessage.success('上移成功')
    await loadCategories(currentModule.value.id)
  } catch (error: any) {
    ElMessage.error(error.message || '上移失败')
  }
}

/**
 * 下移分类
 */
async function handleMoveCategoryDown(category: AdminNavigationModuleCategoryListItem) {
  if (!currentModule.value) return
  try {
    await ApiService.moveNavigationModuleCategoryDown(currentModule.value.id, category.id)
    ElMessage.success('下移成功')
    await loadCategories(currentModule.value.id)
  } catch (error: any) {
    ElMessage.error(error.message || '下移失败')
  }
}

/**
 * 删除分类
 */
async function handleDeleteCategory(category: AdminNavigationModuleCategoryListItem) {
  if (!currentModule.value) return
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

    categoriesLoading.value = true
    try {
      await ApiService.deleteNavigationModuleCategory(currentModule.value.id, category.id)
      ElMessage.success('删除分类成功')
      await loadCategories(currentModule.value.id)
    } catch (error: any) {
      ElMessage.error(error.message || '删除分类失败')
    } finally {
      categoriesLoading.value = false
    }
  } catch {
    // 用户取消
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadModules()
})
</script>

<style scoped>
.admin-navigation-page {
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

.categories-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
</style>
