<template>
  <div class="admin-model-providers-page">
    <div class="page-header">
      <h1>模型供应商配置</h1>
    </div>

    <!-- 供应商列表 -->
    <el-table :data="providers" stripe>
      <el-table-column prop="provider_name" label="供应商名称" width="200" />
      <el-table-column prop="provider_code" label="代码" width="120" />
      <el-table-column prop="base_url" label="API地址" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_enabled ? 'success' : 'info'">
            {{ row.is_enabled ? '启用' : '禁用' }}
          </el-tag>
          <el-tag v-if="row.is_default" type="warning" size="small" style="margin-left: 5px">默认</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button link type="primary" @click="showModelsDialog(row)">模型</el-button>
          <el-button link type="primary" @click="showEditProviderDialog(row)">配置</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 供应商配置对话框 -->
    <el-dialog
      v-model="providerDialogVisible"
      title="供应商配置"
      width="600px"
    >
      <el-form :model="providerForm" label-width="120px">
        <el-form-item label="供应商代码">
          <el-input v-model="providerForm.provider_code" disabled />
        </el-form-item>
        <el-form-item label="供应商名称">
          <el-input v-model="providerForm.provider_name" />
        </el-form-item>
        <el-form-item label="API密钥">
          <el-input v-model="providerForm.api_key" type="password" show-password placeholder="留空则不修改" />
          <div v-if="getApiKeyUrl(providerForm.provider_code)" class="api-key-link">
            <a :href="getApiKeyUrl(providerForm.provider_code)" target="_blank" rel="noopener noreferrer">
              获取 API 密钥 →
            </a>
          </div>
        </el-form-item>
        <el-form-item label="API地址">
          <el-input v-model="providerForm.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="providerForm.order" :min="0" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="providerForm.is_enabled" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="providerForm.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="providerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveProvider">保存</el-button>
      </template>
    </el-dialog>

    <!-- 模型配置对话框 -->
    <el-dialog v-model="modelsDialogVisible" title="模型配置" width="900px">
      <div class="models-header">
        <h3>{{ currentProvider?.provider_name }} - 模型列表</h3>
      </div>
      <el-table :data="models" size="small">
        <el-table-column prop="model_name" label="模型名称" width="180" />
        <el-table-column prop="model_code" label="代码" width="120" />
        <el-table-column prop="capabilities" label="能力" width="120">
          <template #default="{ row }">
            <el-tag v-for="cap in row.capabilities" :key="cap" size="small" style="margin-right: 5px">
              {{ cap }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="积分汇率" width="120">
          <template #default="{ row }">
            <span v-if="getModelPointRate(row.id)">
              {{ getRateDisplay(row.id) }}
            </span>
            <span v-else style="color: #999">未配置</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="70">
          <template #default="{ row }">
            <el-tag :type="row.is_enabled ? 'success' : 'info'" size="small">
              {{ row.is_enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="showEditModelDialog(row)">配置</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 模型配置对话框（简化为单表单） -->
    <el-dialog
      v-model="modelDialogVisible"
      title="模型配置"
      width="600px"
    >
      <el-form :model="modelForm" label-width="100px">
        <el-form-item label="模型代码">
          <el-input v-model="modelForm.model_code" disabled />
        </el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="modelForm.model_name" />
        </el-form-item>
        <el-form-item label="支持能力">
          <el-checkbox-group v-model="modelForm.capabilitiesArray">
            <el-checkbox label="chat">对话</el-checkbox>
            <el-checkbox label="image">图片生成</el-checkbox>
            <el-checkbox label="audio">音频生成</el-checkbox>
            <el-checkbox label="video">视频生成</el-checkbox>
            <el-checkbox label="code">代码</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-divider content-position="left">积分汇率配置</el-divider>

        <el-form-item label="启用汇率">
          <el-switch v-model="pointRateForm.rate_enabled" />
        </el-form-item>
        <el-form-item label="输入汇率">
          <el-input-number
            v-model="pointRateForm.input_rate"
            :min="1"
            :disabled="!pointRateForm.rate_enabled"
            style="width: 200px"
          />
          <span style="margin-left: 10px">tokens / 积分</span>
        </el-form-item>
        <el-form-item label="输出汇率">
          <el-input-number
            v-model="pointRateForm.output_rate"
            :min="1"
            :disabled="!pointRateForm.rate_enabled"
            style="width: 200px"
          />
          <span style="margin-left: 10px">tokens / 积分</span>
        </el-form-item>

        <el-form-item label="启用模型">
          <el-switch v-model="modelForm.is_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveModel" :loading="modelSaving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ApiService } from '@/services/apiClient'
import type {
  ModelProviderListItem,
  ModelConfigListItem,
  UpdateModelProviderRequest,
  ModelPointRateItem,
  CreatePointRateRequest,
  UpdatePointRateRequest
} from '@/types'

const providers = ref<ModelProviderListItem[]>([])
const models = ref<ModelConfigListItem[]>([])
const currentProvider = ref<ModelProviderListItem | null>(null)
const pointRates = ref<ModelPointRateItem[]>([])

// 供应商表单
const providerDialogVisible = ref(false)
const editingProvider = ref<ModelProviderListItem | null>(null)
const providerForm = ref<UpdateModelProviderRequest & { provider_code: string }>({
  provider_code: '',
  provider_name: '',
  api_key: '',
  base_url: '',
  is_enabled: true,
  is_default: false,
  order: 0
})

// 模型表单
const modelsDialogVisible = ref(false)
const modelDialogVisible = ref(false)
const editingModel = ref<ModelConfigListItem | null>(null)
const modelSaving = ref(false)
const modelForm = ref<{
  model_code: string
  model_name: string
  capabilitiesArray: string[]
  is_enabled: boolean
}>({
  model_code: '',
  model_name: '',
  capabilitiesArray: ['chat'],
  is_enabled: true
})

// 汇率表单（简化）
const existingRate = ref<ModelPointRateItem | null>(null)
const pointRateForm = ref<{
  rate_enabled: boolean
  input_rate: number | null
  output_rate: number | null
}>({
  rate_enabled: true,
  input_rate: null,
  output_rate: null
})

// 加载供应商列表
const loadProviders = async () => {
  try {
    const response = await ApiService.getModelProviders(true)
    providers.value = response.providers
  } catch (error) {
    ElMessage.error('加载供应商列表失败')
  }
}

// 加载所有汇率配置
const loadPointRates = async () => {
  try {
    pointRates.value = await ApiService.getModelPointRates()
  } catch (error) {
    console.error('加载汇率配置失败:', error)
  }
}

// 获取模型的汇率配置
const getModelPointRate = (modelId: string): ModelPointRateItem | null => {
  return pointRates.value.find(r => r.model_config_id === modelId) || null
}

// 获取汇率显示文本
const getRateDisplay = (modelId: string): string => {
  const rate = getModelPointRate(modelId)
  if (!rate) return '未配置'
  if (!rate.is_enabled) return '已禁用'
  if (rate.separate_io) {
    return `输入:${rate.tokens_per_point_input} 输出:${rate.tokens_per_point_output}`
  }
  return `${rate.tokens_per_point} tokens/积分`
}

// 显示编辑供应商对话框
const showEditProviderDialog = (provider: ModelProviderListItem) => {
  editingProvider.value = provider
  providerForm.value = {
    provider_code: provider.provider_code,
    provider_name: provider.provider_name,
    api_key: '', // 不回填密码
    base_url: provider.base_url || '',
    is_enabled: provider.is_enabled,
    is_default: provider.is_default,
    order: provider.order
  }
  providerDialogVisible.value = true
}

// 保存供应商
const handleSaveProvider = async () => {
  if (!editingProvider.value) return
  try {
    const requestData: UpdateModelProviderRequest = {}
    if (providerForm.value.provider_name) requestData.provider_name = providerForm.value.provider_name
    if (providerForm.value.api_key) requestData.api_key = providerForm.value.api_key
    if (providerForm.value.base_url) requestData.base_url = providerForm.value.base_url
    if (providerForm.value.is_enabled !== undefined) requestData.is_enabled = providerForm.value.is_enabled
    if (providerForm.value.is_default !== undefined) requestData.is_default = providerForm.value.is_default
    if (providerForm.value.order !== undefined) requestData.order = providerForm.value.order

    await ApiService.updateModelProvider(editingProvider.value.id, requestData)
    ElMessage.success('更新成功')
    providerDialogVisible.value = false
    await loadProviders()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

// 显示模型配置对话框
const showModelsDialog = async (provider: ModelProviderListItem) => {
  currentProvider.value = provider
  try {
    const response = await ApiService.getProviderModels(provider.id, true)
    models.value = response.models
    await loadPointRates()
    modelsDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载模型列表失败')
  }
}

// 显示编辑模型对话框
const showEditModelDialog = (model: ModelConfigListItem) => {
  editingModel.value = model
  modelForm.value = {
    model_code: model.model_code,
    model_name: model.model_name,
    capabilitiesArray: model.capabilities,
    is_enabled: model.is_enabled
  }

  // 加载汇率配置
  const rate = getModelPointRate(model.id)
  if (rate) {
    existingRate.value = rate
    pointRateForm.value = {
      rate_enabled: rate.is_enabled,
      input_rate: rate.tokens_per_point_input || null,
      output_rate: rate.tokens_per_point_output || null
    }
  } else {
    existingRate.value = null
    pointRateForm.value = {
      rate_enabled: true,
      input_rate: null,
      output_rate: null
    }
  }

  modelDialogVisible.value = true
}

// 保存模型配置（包含汇率）
const handleSaveModel = async () => {
  if (!editingModel.value) return

  // 验证汇率
  if (pointRateForm.value.rate_enabled) {
    if (!pointRateForm.value.input_rate || !pointRateForm.value.output_rate) {
      ElMessage.error('启用汇率时，必须设置输入和输出汇率')
      return
    }
  }

  modelSaving.value = true
  try {
    // 1. 更新模型基本信息
    await ApiService.updateModelConfig(editingModel.value.id, {
      model_name: modelForm.value.model_name,
      capabilities: modelForm.value.capabilitiesArray.join(','),
      is_enabled: modelForm.value.is_enabled
    })

    // 2. 处理汇率配置
    if (pointRateForm.value.rate_enabled && pointRateForm.value.input_rate && pointRateForm.value.output_rate) {
      if (existingRate.value) {
        // 更新现有汇率
        await ApiService.updateModelPointRate(existingRate.value.id, {
          separate_io: true,
          tokens_per_point_input: pointRateForm.value.input_rate,
          tokens_per_point_output: pointRateForm.value.output_rate,
          is_enabled: true
        })
      } else {
        // 创建新汇率
        const newRate = await ApiService.createModelPointRate({
          model_config_id: editingModel.value.id,
          tokens_per_point: 1000,
          separate_io: true,
          tokens_per_point_input: pointRateForm.value.input_rate,
          tokens_per_point_output: pointRateForm.value.output_rate
        })
        pointRates.value.push(newRate)
        existingRate.value = newRate
      }
    } else if (existingRate.value) {
      // 禁用汇率配置
      await ApiService.updateModelPointRate(existingRate.value.id, {
        is_enabled: false
      })
    }

    ElMessage.success('保存成功')
    modelDialogVisible.value = false

    // 刷新数据
    await loadPointRates()
    if (currentProvider.value) {
      const response = await ApiService.getProviderModels(currentProvider.value.id, true)
      models.value = response.models
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    modelSaving.value = false
  }
}

// 获取供应商 API 密钥页面 URL
const getApiKeyUrl = (providerCode: string): string => {
  const urlMap: Record<string, string> = {
    'deepseek': 'https://platform.deepseek.com/api_keys',
    'kimi': 'https://platform.moonshot.cn/console/api-keys',
    'moonshot': 'https://platform.moonshot.cn/console/api-keys',
    'openai': 'https://platform.openai.com/api-keys',
    'zhipu': 'https://open.bigmodel.cn/usercenter/apikeys',
    'glm': 'https://open.bigmodel.cn/usercenter/apikeys',
    'doubao': 'https://console.volcengine.com/ark',
    'bytedance': 'https://console.volcengine.com/ark',
    'claude': 'https://console.anthropic.com/settings/keys',
    'anthropic': 'https://console.anthropic.com/settings/keys',
    'google': 'https://aistudio.google.com/app/apikey',
    'gemini': 'https://aistudio.google.com/app/apikey'
  }
  return urlMap[providerCode] || ''
}

onMounted(() => {
  loadProviders()
  loadPointRates()
})
</script>

<style scoped>
.admin-model-providers-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.models-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.models-header h3 {
  margin: 0;
}

.api-key-link {
  margin-top: 5px;
  font-size: 12px;
}

.api-key-link a {
  color: #409eff;
  text-decoration: none;
}

.api-key-link a:hover {
  text-decoration: underline;
}
</style>
