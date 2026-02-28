/**
 * 剪贴板 composable
 * 提供剪贴板复制功能，包含成功提示
 */
import { ref, onUnmounted, getCurrentInstance } from 'vue'

export function useClipboard() {
  const copiedText = ref<string>('')
  const showSuccessToast = ref(false)
  let toastTimer: ReturnType<typeof setTimeout> | null = null

  /**
   * 清除之前的定时器
   */
  function clearToastTimer() {
    if (toastTimer !== null) {
      clearTimeout(toastTimer)
      toastTimer = null
    }
  }

  /**
   * 检查剪贴板 API 是否可用
   */
  function isClipboardAvailable(): boolean {
    return (
      typeof navigator !== 'undefined' &&
      'clipboard' in navigator &&
      'writeText' in navigator.clipboard
    )
  }

  /**
   * 复制文本到剪贴板
   * @param text 要复制的文本
   * @returns 复制是否成功
   */
  async function copy(text: string): Promise<boolean> {
    // 浏览器兼容性检查
    if (!isClipboardAvailable()) {
      console.error('剪贴板 API 在当前浏览器中不可用')
      return false
    }

    try {
      await navigator.clipboard.writeText(text)
      copiedText.value = text
      showSuccessToast.value = true

      // 清除之前的定时器，防止内存泄漏
      clearToastTimer()

      // 设置新的定时器
      toastTimer = setTimeout(() => {
        showSuccessToast.value = false
        toastTimer = null
      }, 2000)

      return true
    } catch (error) {
      console.error('复制失败:', error)
      return false
    }
  }

  // 只在组件实例上下文中注册卸载钩子
  try {
    if (getCurrentInstance()) {
      onUnmounted(() => {
        clearToastTimer()
      })
    }
  } catch {
    // 如果没有组件实例上下文，忽略错误
    // 这可能在测试环境或非组件上下文中使用 composable 时发生
  }

  return {
    copy,
    copiedText,
    showSuccessToast
  }
}
