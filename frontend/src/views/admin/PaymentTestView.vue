<template>
  <div class="payment-test-page">
    <el-card>
      <template #header>
        <h3>支付回调测试</h3>
      </template>

      <el-form :model="formData" label-width="140px">
        <el-form-item label="商户订单号">
          <el-input
            v-model="formData.out_trade_no"
            placeholder="请输入商户订单号"
            clearable
          />
        </el-form-item>

        <el-form-item label="返回码">
          <el-input
            v-model="formData.return_code"
            placeholder="请输入返回码 (如: SUCCESS)"
            clearable
          />
        </el-form-item>

        <el-form-item label="第三方交易号">
          <el-input
            v-model="formData.third_trade_no"
            placeholder="请输入第三方交易号"
            clearable
          />
        </el-form-item>

        <el-form-item label="总金额(分)">
          <el-input-number
            v-model="formData.total_amt"
            :min="0"
            :step="1"
            placeholder="请输入总金额（单位：分）"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            发送测试通知
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import apiClient from '@/services/apiClient'

/**
 * 表单数据
 */
const formData = ref({
  out_trade_no: '',
  return_code: '',
  third_trade_no: '',
  total_amt: 0
})

/**
 * 加载状态
 */
const loading = ref(false)

/**
 * 提交测试通知
 */
async function handleSubmit() {
  // 验证必填字段
  if (!formData.value.out_trade_no) {
    ElMessage.warning('请输入商户订单号')
    return
  }
  if (!formData.value.return_code) {
    ElMessage.warning('请输入返回码')
    return
  }

  loading.value = true
  try {
    const response = await apiClient.post('/admin/payment/test-notify', {
      out_trade_no: formData.value.out_trade_no,
      return_code: formData.value.return_code,
      third_trade_no: formData.value.third_trade_no,
      total_amt: String(formData.value.total_amt)
    })

    ElMessage.success('测试通知发送成功')
    console.log('响应:', response.data)
  } catch (error: any) {
    ElMessage.error(error.message || '发送失败')
  } finally {
    loading.value = false
  }
}

/**
 * 重置表单
 */
function handleReset() {
  formData.value = {
    out_trade_no: '',
    return_code: '',
    third_trade_no: '',
    total_amt: 0
  }
}
</script>

<style scoped>
.payment-test-page {
  padding: 20px;
}
</style>
