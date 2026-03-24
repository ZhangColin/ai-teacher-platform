<template>
  <div class="model-rates-page">
    <div class="page-header">
      <h1>模型汇率配置</h1>
      <div class="header-actions">
        <el-button @click="handleReset" :disabled="!hasChanges">重置</el-button>
        <el-button type="primary" @click="handleSave" :disabled="!hasChanges" :loading="saving">
          保存
        </el-button>
      </div>
    </div>

    <el-alert
      type="info"
      :closable="false"
      style="margin-bottom: 20px"
    >
      在此页面可以批量设置所有已启用模型的输入/输出汇率。只有被修改的模型会被保存。
    </el-alert>

    <el-card v-loading="loading">
      <ModelRateCollapse
        v-if="!loading && Object.keys(groupedRates).length > 0"
        :grouped-rates="groupedRates"
        @change="handleItemChange"
      />
      <el-empty v-else-if="!loading" description="暂无已启用的模型" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ApiService } from '@/services/apiClient'
import type { GroupedRates, ModelRateFormItem, BatchUpdateRateRequest } from '@/types'
import ModelRateCollapse from '@/components/admin/ModelRateCollapse.vue'

const loading = ref(false)
const saving = ref(false)
const rateItems = ref<ModelRateFormItem[]>([])
const originalItems = ref<ModelRateFormItem[]>([])

// 分组数据
const groupedRates = computed<GroupedRates>(() => {
  const groups: GroupedRates = {}

  rateItems.value.forEach(item => {
    if (!groups[item.provider_id]) {
      groups[item.provider_id] = {
        provider_name: item.provider_name,
        provider_code: item.provider_code,
        models: []
      }
    }
    const group = groups[item.provider_id]
    if (group) {
      group.models.push(item)
    }
  })

  return groups
})

// 是否有变化
const hasChanges = computed(() => {
  return rateItems.value.some(item => item._modified)
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const data = await ApiService.getModelRatesStatus()

    rateItems.value = data.map(item => {
      const formItem: ModelRateFormItem = {
        model_config_id: item.model_config_id,
        model_name: item.model_name,
        model_code: item.model_code,
        provider_id: item.provider_id,
        provider_code: item.provider_code,
        provider_name: item.provider_name,
        tokens_per_point_input: item.rate_config?.tokens_per_point_input ?? undefined,
        tokens_per_point_output: item.rate_config?.tokens_per_point_output ?? undefined,
        is_enabled: item.rate_config?.is_enabled ?? true,
        has_existing_config: item.rate_config !== null &&
          item.rate_config.tokens_per_point_input !== null &&
          item.rate_config.tokens_per_point_output !== null,
        rate_id: item.rate_config?.id,
        _modified: false,
        _original: item.rate_config ? {
          tokens_per_point_input: item.rate_config.tokens_per_point_input ?? undefined,
          tokens_per_point_output: item.rate_config.tokens_per_point_output ?? undefined,
          is_enabled: item.rate_config.is_enabled
        } : undefined
      }
      return formItem
    })

    // 保存原始数据副本
    originalItems.value = JSON.parse(JSON.stringify(rateItems.value))
  } catch (error) {
    console.error('加载模型汇率数据失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 处理单项变化
const handleItemChange = (_item: ModelRateFormItem) => {
  // 变化标记已在组件中处理
}

// 重置
const handleReset = () => {
  rateItems.value = JSON.parse(JSON.stringify(originalItems.value))
  ElMessage.info('已重置所有修改')
}

// 保存
const handleSave = async () => {
  // 验证：启用的模型必须有汇率值
  const modifiedItems = rateItems.value.filter(item => item._modified)

  for (const item of modifiedItems) {
    if (item.is_enabled) {
      if (!item.tokens_per_point_input || !item.tokens_per_point_output) {
        ElMessage.error(`模型 ${item.model_name} 启用时必须设置输入和输出汇率`)
        return
      }
    }
  }

  saving.value = true
  try {
    const request: BatchUpdateRateRequest = {
      updates: modifiedItems.map(item => ({
        model_config_id: item.model_config_id,
        tokens_per_point_input: item.tokens_per_point_input!,
        tokens_per_point_output: item.tokens_per_point_output!,
        is_enabled: item.is_enabled
      }))
    }

    const response = await ApiService.batchUpdateModelRates(request)
    ElMessage.success(`已成功更新 ${response.updated} 个模型的汇率配置`)

    // 重新加载数据
    await loadData()
  } catch (error: any) {
    console.error('保存失败:', error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.model-rates-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.header-actions {
  display: flex;
  gap: 10px;
}
</style>
