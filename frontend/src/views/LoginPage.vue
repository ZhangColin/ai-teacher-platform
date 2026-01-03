<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Logo和平台名称 -->
      <div class="login-header">
        <img src="@/assets/logo/logo.png" alt="海创元AI教育平台" class="login-logo" />
        <h1 class="login-title">海创元AI教育平台</h1>
      </div>

      <!-- 登录表单 -->
      <form @submit.prevent="handleSubmit" class="login-form">
        <!-- 账号输入框（支持邮箱或手机号） -->
        <div class="form-group">
          <label for="account" class="form-label">账号</label>
          <input
            id="account"
            v-model="formData.account"
            type="text"
            class="form-input"
            :class="{ 'form-input-error': errors.account }"
            placeholder="请输入用户名、邮箱或手机号"
            @blur="validateAccount"
          />
          <span v-if="errors.account" class="error-message">{{ errors.account }}</span>
        </div>

        <!-- 密码输入框 -->
        <div class="form-group">
          <label for="password" class="form-label">密码</label>
          <input
            id="password"
            v-model="formData.password"
            type="password"
            class="form-input"
            :class="{ 'form-input-error': errors.password }"
            placeholder="请输入密码"
            @blur="validatePassword"
          />
          <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
        </div>

        <!-- 记住我 -->
        <div class="form-group">
          <label class="checkbox-label">
            <input
              v-model="formData.rememberMe"
              type="checkbox"
              class="checkbox-input"
            />
            <span class="checkbox-text">记住我</span>
          </label>
        </div>

        <!-- 错误提示 -->
        <div v-if="authStore.error" class="error-alert">
          {{ authStore.error }}
        </div>

        <!-- 登录按钮 -->
        <button
          type="submit"
          class="login-button"
          :disabled="authStore.loading"
        >
          <span v-if="authStore.loading">登录中...</span>
          <span v-else>登录</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import type { LoginRequest } from '@/types'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 表单数据
const formData = ref<LoginRequest>({
  account: '',
  password: '',
  remember_me: false,
})

// 表单验证错误
const errors = ref<{
  account?: string
  password?: string
}>({})

// 验证账号格式（用户名、邮箱或手机号）
function validateAccount() {
  const account = formData.value.account.trim()
  if (!account) {
    errors.value.account = '请输入账号'
    return false
  }
  
  // 邮箱格式：^[^@]+@[^@]+\.[^@]+$
  const emailRegex = /^[^@]+@[^@]+\.[^@]+$/
  // 手机号格式：^1[3-9]\d{9}$
  const phoneRegex = /^1[3-9]\d{9}$/
  // 用户名格式：1-50个字符，允许字母、数字、下划线、中文字符等（更宽松）
  // 只要不是邮箱格式和手机号格式，就认为是用户名
  const isEmail = emailRegex.test(account)
  const isPhone = phoneRegex.test(account)
  const isUsername = !isEmail && !isPhone && account.length >= 1 && account.length <= 50
  
  if (!isEmail && !isPhone && !isUsername) {
    errors.value.account = '请输入正确的用户名、邮箱或手机号'
    return false
  }
  
  delete errors.value.account
  return true
}

// 验证密码
function validatePassword() {
  const password = formData.value.password
  if (!password) {
    errors.value.password = '请输入密码'
    return false
  }
  if (password.length < 6) {
    errors.value.password = '密码至少需要6位'
    return false
  }
  delete errors.value.password
  return true
}

// 表单是否有效
const isFormValid = computed(() => {
  return (
    formData.value.account.trim() !== '' &&
    formData.value.password.length >= 6 &&
    Object.keys(errors.value).length === 0
  )
})

// 提交登录
async function handleSubmit() {
  // 验证表单
  const accountValid = validateAccount()
  const passwordValid = validatePassword()
  
  if (!accountValid || !passwordValid) {
    return
  }

  // 清除之前的错误
  authStore.error = null

  try {
    await authStore.login({
      account: formData.value.account.trim(),
      password: formData.value.password,
      remember_me: formData.value.remember_me,
    })

    // 登录成功，跳转到原访问页面或首页
    const redirect = route.query.redirect as string | undefined
    router.push(redirect || '/modules/ai-tools')
  } catch (err) {
    // 错误已在authStore中处理
    console.error('登录失败:', err)
  }
}
</script>

<style scoped>
.login-page {
  @apply min-h-screen flex items-center justify-center;
  background: linear-gradient(to bottom, theme('colors.gray.50') 0%, theme('colors.gray.100') 100%);
}

.login-container {
  @apply w-full max-w-md px-6 py-8 bg-white rounded-xl shadow-lg;
}

.login-header {
  @apply text-center mb-8;
}

.login-logo {
  @apply h-16 w-auto mx-auto mb-4;
  object-fit: contain;
}

.login-title {
  @apply text-2xl font-semibold text-gray-900;
}

.login-form {
  @apply space-y-6;
}

.form-group {
  @apply space-y-2;
}

.form-label {
  @apply block text-sm font-medium text-gray-700;
}

.form-input {
  @apply w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all;
}

.form-input-error {
  @apply border-error-500 focus:ring-error-500;
}

.error-message {
  @apply text-sm text-error-600;
}

.checkbox-label {
  @apply flex items-center cursor-pointer;
}

.checkbox-input {
  @apply w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500;
}

.checkbox-text {
  @apply ml-2 text-sm text-gray-700;
}

.error-alert {
  @apply px-4 py-3 bg-error-50 border border-error-200 rounded-lg text-sm text-error-800;
}

.login-button {
  @apply w-full px-4 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed;
}

/* 平板端响应式 */
@media (min-width: 768px) and (max-width: 1023px) {
  .login-container {
    @apply max-w-lg;
  }
}

/* 移动端响应式 */
@media (max-width: 767px) {
  .login-container {
    @apply px-4 py-6;
  }
  
  .login-logo {
    @apply h-12;
  }
  
  .login-title {
    @apply text-xl;
  }
}
</style>

