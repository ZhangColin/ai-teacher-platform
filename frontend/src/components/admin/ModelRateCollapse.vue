<template>
  <div class="model-rate-collapse">
    <el-collapse v-model="activeProviderIds" @change="handleCollapseChange">
      <el-collapse-item
        v-for="(group, providerId) in groupedRates"
        :key="providerId"
        :name="providerId"
      >
        <template #title>
          <div class="provider-header">
            <span class="provider-name">{{ group.provider_name }} ({{ group.models.length }} 个模型)</span>
            <span class="provider-code">{{ group.provider_code }}</span>
          </div>
        </template>

        <el-table :data="group.models" size="small" class="rate-table">
          <el-table-column prop="model_name" label="模型名称" width="180" />
          <el-table-column prop="model_code" label="代码" width="150" />

          <el-table-column label="输入汇率" width="160">
            <template #default="{ row }">
              <el-input-number
                v-model="row.tokens_per_point_input"
                :min="1"
                :disabled="!row.is_enabled"
                size="small"
                @change="handleRateChange(row)"
              />
              <span class="unit">tokens/积分</span>
            </template>
          </el-table-column>

          <el-table-column label="输出汇率" width="160">
            <template #default="{ row }">
              <el-input-number
                v-model="row.tokens_per_point_output"
                :min="1"
                :disabled="!row.is_enabled"
                size="small"
                @change="handleRateChange(row)"
              />
              <span class="unit">tokens/积分</span>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-switch v-model="row.is_enabled" @change="handleRateChange(row)" />
            </template>
          </el-table-column>

          <el-table-column label="配置状态" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.has_existing_config" type="success" size="small">已配置</el-tag>
              <el-tag v-else type="info" size="small">未配置</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { GroupedRates, ModelRateFormItem } from '@/types'

interface Props {
  groupedRates: GroupedRates
  modelValue?: ModelRateFormItem[]
}

interface Emits {
  (e: 'update:modelValue', value: ModelRateFormItem[]): void
  (e: 'change', item: ModelRateFormItem): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const activeProviderIds = ref<string[]>([])

// 默认展开第一个供应商
watch(() => props.groupedRates, (newRates) => {
  const keys = Object.keys(newRates)
  if (keys.length > 0 && activeProviderIds.value.length === 0) {
    activeProviderIds.value = [keys[0]]
  }
}, { immediate: true })

const handleCollapseChange = () => {
  // 折叠面板变化时的处理
}

const handleRateChange = (row: ModelRateFormItem) => {
  // 标记为已修改
  if (!row._original) {
    row._original = {
      tokens_per_point_input: undefined,
      tokens_per_point_output: undefined,
      is_enabled: false
    }
  }

  // 检查是否真的有变化
  const hasChanged =
    row._original.tokens_per_point_input !== row.tokens_per_point_input ||
    row._original.tokens_per_point_output !== row.tokens_per_point_output ||
    row._original.is_enabled !== row.is_enabled

  row._modified = hasChanged
  emit('change', row)
}
</script>

<style scoped>
.model-rate-collapse {
  padding: 10px 0;
}

.provider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding-right: 20px;
}

.provider-name {
  font-weight: 500;
}

.provider-code {
  color: #999;
  font-size: 12px;
}

.rate-table {
  margin-top: 10px;
}

.unit {
  margin-left: 5px;
  font-size: 12px;
  color: #999;
}
</style>
