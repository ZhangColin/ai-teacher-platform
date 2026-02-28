/**
 * 剪贴板 composable
 * 提供剪贴板复制功能，包含成功提示
 */
import { ref } from 'vue'

export function useClipboard() {
  const copiedText = ref<string>('')
  const showSuccessToast = ref(false)

  /**
   * 复制文本到剪贴板
   * @param text 要复制的文本
   * @returns 复制是否成功
   */
  async function copy(text: string): Promise<boolean> {
    try {
      await navigator.clipboard.writeText(text)
      copiedText.value = text
      showSuccessToast.value = true

      setTimeout(() => {
        showSuccessToast.value = false
      }, 2000)

      return true
    } catch (error) {
      console.error('复制失败:', error)
      return false
    }
  }

  return {
    copy,
    copiedText,
    showSuccessToast
  }
}
