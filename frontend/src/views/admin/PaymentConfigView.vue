<template>
  <div class="payment-config-page">
    <el-card>
      <template #header>
        <h3>支付配置管理</h3>
      </template>

      <el-form :model="configForm" label-width="150px" style="max-width: 600px">
        <el-form-item label="积分兑换比例">
          <el-input-number
            v-model="configForm.points_per_yuan"
            :min="1"
            :max="10000"
            :step="1"
          />
          <span class="unit">积分/元</span>
          <div class="form-tip">
            设置 1 元人民币对应的积分数，例如设置为 100 表示充值 1 元获得 100 积分
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="saving">
            保存配置
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 配置说明 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <h4>配置说明</h4>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="积分兑换比例">
          控制用户充值时获得的积分数量。例如设置为 100，用户充值 10 元将获得 1000 积分。
        </el-descriptions-item>
        <el-descriptions-item label="充值金额范围">
          用户单次充值金额范围为 1 元 - 5000 元。
        </el-descriptions-item>
        <el-descriptions-item label="支付超时时间">
          订单超时时间为 15 分钟，超时后订单自动取消。
        </el-descriptions-item>
        <el-descriptions-item label="支付回调">
          支付成功后，工行会通过回调接口通知系统，系统自动增加用户企业积分。
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '@/services/apiClient'

// 配置表单
const configForm = ref({
  points_per_yuan: 100
})

// 原始配置（用于重置）
const originalConfig = ref({
  points_per_yuan: 100
})

// 保存中
const saving = ref(false)

/**
 * 加载配置
 */
async function loadConfig() {
  try {
    const response = await apiClient.get('/admin/payment/config')
    configForm.value = {
      points_per_yuan: response.data.points_per_yuan || 100
    }
    originalConfig.value = { ...configForm.value }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载配置失败')
  }
}

/**
 * 保存配置
 */
async function handleSave() {
  saving.value = true
  try {
    await apiClient.post('/admin/payment/config', {
      points_per_yuan: configForm.value.points_per_yuan
    })
    ElMessage.success('配置保存成功')
    originalConfig.value = { ...configForm.value }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存配置失败')
  } finally {
    saving.value = false
  }
}

/**
 * 重置
 */
function handleReset() {
  configForm.value = { ...originalConfig.value }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.payment-config-page {
  max-width: 900px;
}

.unit {
  margin-left: 8px;
  color: #606266;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
  line-height: 1.5;
}
</style>
