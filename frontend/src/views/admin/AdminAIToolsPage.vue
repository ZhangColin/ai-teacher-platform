<template>
  <div class="admin-ai-tools-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <h3>AI工具管理</h3>
          <el-button type="primary" @click="handleCreate">创建工具</el-button>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filter-bar">
        <el-select
          v-model="filterNavigationModuleId"
          placeholder="筛选导航模块"
          clearable
          @change="handleFilterChange"
          style="width: 200px"
        >
          <el-option
            v-for="module in navigationModules"
            :key="module.id"
            :label="module.name"
            :value="module.id"
          />
        </el-select>
        <el-select
          v-model="filterCategoryId"
          placeholder="筛选分类"
          clearable
          @change="handleFilterChange"
          style="width: 200px"
          :disabled="!filterNavigationModuleId"
        >
          <el-option
            v-for="category in categories"
            :key="category.id"
            :label="category.name"
            :value="category.id"
          />
        </el-select>
        <el-select
          v-model="filterVisible"
          placeholder="筛选可见性"
          clearable
          @change="handleFilterChange"
          style="width: 150px"
        >
          <el-option label="全部" :value="undefined" />
          <el-option label="可见" :value="true" />
          <el-option label="隐藏" :value="false" />
        </el-select>
      </div>

      <!-- 工具列表表格 -->
      <el-table :data="tools" v-loading="loading" style="width: 100%; margin-top: 16px">
        <el-table-column prop="order" label="排序" width="80" />
        <el-table-column label="图标" width="80">
          <template #default="{ row }">
            <HeroIcon v-if="row.icon" :icon-name="row.icon" class="w-6 h-6" />
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="navigation_module_name" label="导航模块" width="150" />
        <el-table-column prop="category_name" label="分类" width="150">
          <template #default="{ row }">
            {{ row.category_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="tool_id" label="工具ID" width="180" />
        <el-table-column prop="name" label="工具名称" width="180" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'normal' ? 'primary' : 'info'" size="small">
              {{ row.type === 'normal' ? '普通' : '占位' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="可见" width="80">
          <template #default="{ row }">
            <el-switch
              :model-value="row.visible"
              @change="handleToggleVisibility(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
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

    <!-- 创建/编辑工具抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="isEditing ? '编辑AI工具' : '创建AI工具'"
      size="70%"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="140px">
        <el-divider content-position="left">基本信息</el-divider>
        <el-form-item label="所属导航模块" prop="navigation_module_id">
          <el-select
            v-model="form.navigation_module_id"
            placeholder="请选择导航模块"
            style="width: 100%"
            @change="handleNavigationModuleChange"
          >
            <el-option
              v-for="module in navigationModules"
              :key="module.id"
              :label="module.name"
              :value="module.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-select
            v-model="form.category_id"
            placeholder="请选择分类"
            style="width: 100%"
          >
            <el-option
              v-for="category in availableCategories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="工具ID" prop="tool_id">
          <el-input
            v-model="form.tool_id"
            placeholder="请输入工具唯一标识符（如：lesson_planner）"
            :disabled="isEditing"
          />
          <div class="text-xs text-gray-500 mt-1">创建后不可修改</div>
        </el-form-item>
        <el-form-item label="工具名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入工具名称" />
        </el-form-item>
        <el-form-item label="工具描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入工具描述"
          />
        </el-form-item>
        <el-form-item label="图标">
          <IconSelector v-model="form.icon" />
        </el-form-item>
        <el-form-item label="工具类型">
          <el-radio-group v-model="form.type">
            <el-radio value="normal">普通工具</el-radio>
            <el-radio value="placeholder">占位工具</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="内容类型">
          <el-radio-group v-model="form.content_type">
            <el-radio value="text">文本</el-radio>
            <el-radio value="multimodal">多模态</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="媒体类型" v-if="form.content_type === 'multimodal'">
          <el-select v-model="form.media_type" placeholder="请选择媒体类型">
            <el-option label="图片" value="image" />
            <el-option label="音频" value="audio" />
            <el-option label="视频" value="video" />
          </el-select>
        </el-form-item>
        <el-form-item label="所需 AI 能力">
          <el-select v-model="form.required_capability" placeholder="请选择所需 AI 能力">
            <el-option label="文字对话 (chat)" value="chat" />
            <el-option label="图像生成 (image)" value="image" />
            <el-option label="音频生成 (audio)" value="audio" />
            <el-option label="视频生成 (video)" value="video" />
            <el-option label="代码生成 (code)" value="code" />
          </el-select>
        </el-form-item>
        <el-form-item label="AI模型">
          <el-select
            v-model="form.model"
            placeholder="选择AI模型（留空使用默认）"
            filterable
            allow-create
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="model in availableModels"
              :key="`${model.provider_code}:${model.model_code}`"
              :label="`${model.provider_name} - ${model.model_name}`"
              :value="`${model.provider_code}:${model.model_code}`"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="欢迎语">
          <el-input
            v-model="form.welcome_message"
            type="textarea"
            :rows="3"
            placeholder="请输入欢迎语（可选）"
          />
        </el-form-item>
        <el-form-item label="可见性">
          <el-switch v-model="form.visible" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.order" :min="0" :max="999" />
        </el-form-item>

        <el-divider content-position="left">系统提示词</el-divider>
        <el-form-item label="系统提示词" prop="system_prompt">
          <div class="w-full">
            <div class="flex justify-end mb-2">
              <el-button size="small" @click="promptEditorFullscreen = true">
                全屏编辑
              </el-button>
            </div>
            <MarkdownEditor v-model="form.system_prompt" />
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="drawer-footer">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEditing ? '保存' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 全屏提示词编辑器对话框 -->
    <el-dialog
      v-model="promptEditorFullscreen"
      title="编辑系统提示词"
      width="90%"
      :close-on-click-modal="false"
      fullscreen
    >
      <MarkdownEditor v-model="form.system_prompt" :fullscreen="true" />
      <template #footer>
        <el-button @click="promptEditorFullscreen = false">完成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ApiService } from '../../services/apiClient'
import type {
  AdminAIToolListItem,
  AdminNavigationModuleListItem,
  AdminNavigationModuleCategoryListItem,
  CreateAIToolRequest,
  UpdateAIToolRequest,
  ModelConfigListItem,
} from '../../types'
import IconSelector from '../../components/admin/IconSelector.vue'
import HeroIcon from '../../components/HeroIcon.vue'
import MarkdownEditor from '../../components/editor/MarkdownEditor.vue'

// 工具列表
const tools = ref<AdminAIToolListItem[]>([])
const navigationModules = ref<AdminNavigationModuleListItem[]>([])
const categories = ref<AdminNavigationModuleCategoryListItem[]>([])
const availableModels = ref<ModelConfigListItem[]>([])
const loading = ref(false)

// 筛选器
const filterNavigationModuleId = ref<string>()
const filterCategoryId = ref<string>()
const filterVisible = ref<boolean>()

// 抽屉
const drawerVisible = ref(false)
const isEditing = ref(false)
const formRef = ref<FormInstance>()
const submitting = ref(false)
const promptEditorFullscreen = ref(false)

// 表单数据
const form = reactive<CreateAIToolRequest & { id?: string }>({
  tool_id: '',
  navigation_module_id: '',
  category_id: '',
  name: '',
  description: '',
  system_prompt: '',
  icon: '',
  type: 'normal',
  content_type: 'text',
  media_type: undefined,
  required_capability: 'chat',
  model: '',
  welcome_message: '',
  visible: true,
  order: 0,
})

// 可用分类列表（根据选中的导航模块过滤）
const availableCategories = computed(() => {
  if (!form.navigation_module_id) return []
  return categories.value.filter((c) => c.navigation_module_id === form.navigation_module_id)
})

// 表单验证规则
const rules: FormRules = {
  navigation_module_id: [{ required: true, message: '请选择所属导航模块', trigger: 'change' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  tool_id: [
    { required: true, message: '请输入工具ID', trigger: 'blur' },
    {
      pattern: /^[a-z0-9_]+$/,
      message: '工具ID只能包含小写字母、数字和下划线',
      trigger: 'blur',
    },
  ],
  name: [
    { required: true, message: '请输入工具名称', trigger: 'blur' },
    { min: 1, max: 50, message: '工具名称长度为1-50个字符', trigger: 'blur' },
  ],
  description: [
    { required: true, message: '请输入工具描述', trigger: 'blur' },
    { max: 500, message: '工具描述长度不能超过500个字符', trigger: 'blur' },
  ],
  system_prompt: [
    { required: true, message: '请输入系统提示词', trigger: 'blur' },
  ],
}

/**
 * 加载导航模块列表
 */
async function loadNavigationModules() {
  try {
    const response = await ApiService.getAdminNavigationModules()
    navigationModules.value = response.modules
  } catch (error: any) {
    ElMessage.error(error.message || '加载导航模块列表失败')
  }
}

/**
 * 加载分类列表
 */
async function loadCategories() {
  try {
    const response = await ApiService.getAdminNavigationModuleCategories(
      filterNavigationModuleId.value || ''
    )
    categories.value = response.categories
  } catch (error: any) {
    ElMessage.error(error.message || '加载分类列表失败')
  }
}

/**
 * 加载工具列表
 */
async function loadTools() {
  loading.value = true
  try {
    const response = await ApiService.getAdminAITools(
      filterNavigationModuleId.value,
      filterCategoryId.value,
      filterVisible.value
    )
    tools.value = response.tools
  } catch (error: any) {
    ElMessage.error(error.message || '加载工具列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 筛选变化
 */
async function handleFilterChange() {
  // 当导航模块筛选变化时，清空分类筛选并重新加载分类
  if (filterNavigationModuleId.value) {
    await loadCategories()
    // 如果当前选中的分类不在新导航模块下，清空
    const moduleCategories = categories.value.filter(
      (c) => c.navigation_module_id === filterNavigationModuleId.value
    )
    if (
      filterCategoryId.value &&
      !moduleCategories.find((c) => c.id === filterCategoryId.value)
    ) {
      filterCategoryId.value = undefined
    }
  } else {
    filterCategoryId.value = undefined
    categories.value = []
  }

  loadTools()
}

/**
 * 导航模块变化时清空分类并重新加载分类
 */
async function handleNavigationModuleChange() {
  form.category_id = ''
  if (form.navigation_module_id) {
    try {
      const response = await ApiService.getAdminNavigationModuleCategories(
        form.navigation_module_id
      )
      categories.value = response.categories
    } catch (error: any) {
      ElMessage.error(error.message || '加载分类列表失败')
    }
  } else {
    categories.value = []
  }
}

/**
 * 创建工具
 */
function handleCreate() {
  isEditing.value = false
  Object.assign(form, {
    tool_id: '',
    navigation_module_id: filterNavigationModuleId.value || '',
    category_id: filterCategoryId.value || '',
    name: '',
    description: '',
    system_prompt: '',
    icon: '',
    type: 'normal',
    content_type: 'text',
    media_type: undefined,
    required_capability: 'chat',
    model: '',
    welcome_message: '',
    visible: true,
    order: tools.value.length,
  })
  formRef.value?.clearValidate()
  drawerVisible.value = true
}

/**
 * 编辑工具
 */
async function handleEdit(tool: AdminAIToolListItem) {
  isEditing.value = true
  // 加载该导航模块的分类
  if (tool.navigation_module_id) {
    try {
      const response = await ApiService.getAdminNavigationModuleCategories(
        tool.navigation_module_id
      )
      categories.value = response.categories
    } catch (error: any) {
      ElMessage.error(error.message || '加载分类列表失败')
    }
  }
  Object.assign(form, {
    id: tool.id,
    tool_id: tool.tool_id,
    navigation_module_id: tool.navigation_module_id,
    category_id: tool.category_id || '',
    name: tool.name,
    description: tool.description,
    system_prompt: tool.system_prompt,
    icon: tool.icon || '',
    type: tool.type,
    content_type: tool.content_type,
    media_type: tool.media_type,
    required_capability: tool.required_capability || 'chat',
    model: tool.model || '',
    welcome_message: tool.welcome_message || '',
    visible: tool.visible,
    order: tool.order,
  })
  formRef.value?.clearValidate()
  drawerVisible.value = true
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
        await ApiService.updateAITool(form.tool_id, requestData as UpdateAIToolRequest)
        ElMessage.success('更新工具成功')
      } else {
        // 创建
        await ApiService.createAITool(form as CreateAIToolRequest)
        ElMessage.success('创建工具成功')
      }
      drawerVisible.value = false
      loadTools()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

/**
 * 上移工具
 */
async function handleMoveUp(tool: AdminAIToolListItem) {
  try {
    await ApiService.moveAIToolUp(tool.tool_id)
    ElMessage.success('上移成功')
    loadTools()
  } catch (error: any) {
    ElMessage.error(error.message || '上移失败')
  }
}

/**
 * 下移工具
 */
async function handleMoveDown(tool: AdminAIToolListItem) {
  try {
    await ApiService.moveAIToolDown(tool.tool_id)
    ElMessage.success('下移成功')
    loadTools()
  } catch (error: any) {
    ElMessage.error(error.message || '下移失败')
  }
}

/**
 * 切换可见性
 */
async function handleToggleVisibility(tool: AdminAIToolListItem) {
  try {
    await ApiService.toggleAIToolVisibility(tool.tool_id)
    ElMessage.success('切换可见性成功')
    loadTools()
  } catch (error: any) {
    ElMessage.error(error.message || '切换可见性失败')
  }
}

/**
 * 删除工具
 */
async function handleDelete(tool: AdminAIToolListItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除工具 "${tool.name}" 吗？删除后无法恢复。`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    loading.value = true
    try {
      await ApiService.deleteAITool(tool.tool_id)
      ElMessage.success('删除工具成功')
      loadTools()
    } catch (error: any) {
      ElMessage.error(error.message || '删除工具失败')
    } finally {
      loading.value = false
    }
  } catch {
    // 用户取消
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadNavigationModules()
  loadTools()
  // 默认加载 chat 能力的模型
  loadAvailableModels(form.required_capability)
})

// 加载可用模型列表
const loadAvailableModels = async (capability?: string) => {
  try {
    const response = await ApiService.getAvailableModelsFromDB(undefined, capability)
    availableModels.value = response.models
  } catch (error) {
    console.error('加载可用模型失败:', error)
  }
}

// 监听 AI 能力变化，过滤模型列表
watch(() => form.required_capability, (newCapability) => {
  console.log('[AdminAITools] required_capability 变化:', newCapability)
  loadAvailableModels(newCapability || undefined)
})
</script>

<style scoped>
.admin-ai-tools-page {
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

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 0;
}
</style>
